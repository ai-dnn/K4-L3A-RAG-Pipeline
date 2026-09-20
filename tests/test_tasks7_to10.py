import copy
import json
from types import SimpleNamespace

import pytest
import requests

from src import task7_reranking as fusion
from src import task8_pageindex_vectorless as pageindex
from src import task9_retrieval_pipeline as pipeline
from src import task10_generation as generation
from src import llm
from src.contracts import validate_generation_result, validate_search_results


def result(item_id='a', score=0.9, method='dense'):
    return {'id': item_id, 'content': 'Người lao động được nghỉ hằng năm.', 'score': score,
            'metadata': {'source': 'law.docx', 'title': 'Bộ luật Lao động', 'doc_type': 'legal',
                         'url': None, 'chunk_index': 0}, 'retrieval_method': method}


def test_rrf_duplicates_nonmutation_and_empty():
    lists = [[result(), result(), result('b')], [result('b', 10, 'bm25')]]
    original = copy.deepcopy(lists)
    output = fusion.rerank_rrf(lists)
    validate_search_results(output, expected_method='hybrid')
    assert output[0]['id'] == 'b'
    assert output[0]['score'] == pytest.approx(1 / 63 + 1 / 61)
    assert output[1]['score'] == pytest.approx(1 / 61)
    assert lists == original
    assert fusion.rerank_rrf([]) == []
    assert fusion.rerank_rrf(lists, top_k=0) == []
    with pytest.raises(ValueError):
        fusion.rerank_rrf(lists, k=-1)


def test_dense_baseline_skips_bm25_and_fusion(monkeypatch):
    monkeypatch.setattr(pipeline, 'semantic_search', lambda *args, **kwargs: [result()])
    monkeypatch.setattr(pipeline, 'lexical_search', lambda *args, **kwargs: pytest.fail('BM25 called'))
    monkeypatch.setattr(pipeline, 'rerank_rrf', lambda *args, **kwargs: pytest.fail('RRF called'))
    assert pipeline.retrieve('lao động', use_reranking=False)[0]['retrieval_method'] == 'dense'
    assert pipeline.retrieve(' ', top_k=3) == []


def test_fallback_empty_keeps_hybrid(monkeypatch):
    monkeypatch.setattr(pipeline, 'semantic_search', lambda *args, **kwargs: [result(score=0.1)])
    monkeypatch.setattr(pipeline, 'lexical_search', lambda *args, **kwargs: [])
    monkeypatch.setattr(pipeline, 'pageindex_search', lambda *args, **kwargs: [])
    assert pipeline.retrieve('lao động', score_threshold=0.5)[0]['retrieval_method'] == 'hybrid'


def test_pageindex_disabled_never_calls_network(monkeypatch):
    monkeypatch.delenv('PAGEINDEX_API_KEY', raising=False)
    monkeypatch.setattr(pageindex.requests, 'get', lambda *args, **kwargs: pytest.fail('Network called'))
    monkeypatch.setattr(pageindex.requests, 'post', lambda *args, **kwargs: pytest.fail('Network called'))
    assert pageindex.pageindex_search('lao động') == []
    pageindex.upload_documents()


@pytest.fixture
def pageindex_cache(tmp_path, monkeypatch):
    document = {'id': 'legal/law.md', 'content': 'Điều 113. Nghỉ hằng năm', 'metadata': result()['metadata']}
    cache = tmp_path / 'cache.json'
    cache.write_text(json.dumps({document['id']: {
        'doc_id': 'pi-123', 'sha256': pageindex._document_hash(document), 'metadata': document['metadata'],
    }}))
    monkeypatch.setenv('PAGEINDEX_API_KEY', 'test-key')
    monkeypatch.setattr(pageindex, 'CACHE_PATH', cache)
    monkeypatch.setattr(pageindex, 'PDF_DIR', tmp_path / 'pdf')
    monkeypatch.setattr(pageindex, 'load_documents', lambda: [document])
    return document, cache


def test_pageindex_upload_cache_and_content_change(pageindex_cache, monkeypatch):
    document, cache = pageindex_cache
    calls = []
    monkeypatch.setattr(pageindex, '_write_pdf', lambda doc, path: path.write_bytes(b'%PDF-test'))

    def post(url, **kwargs):
        assert url.endswith('/doc/')
        assert kwargs['timeout'] == (10, 120)
        assert not kwargs['files']['file'][1].closed
        calls.append(url)
        return SimpleNamespace(raise_for_status=lambda: None, json=lambda: {'doc_id': 'pi-new'})

    monkeypatch.setattr(pageindex.requests, 'post', post)
    pageindex.upload_documents()
    assert calls == []
    document['content'] += ' Nội dung đã cập nhật'
    pageindex.upload_documents()
    pageindex.upload_documents()
    assert len(calls) == 1
    assert json.loads(cache.read_text())[document['id']]['doc_id'] == 'pi-new'


def test_pageindex_selects_original_tree_text(pageindex_cache, monkeypatch):
    def get(url, **kwargs):
        assert url == 'https://api.pageindex.ai/doc/pi-123/'
        assert kwargs['params'] == {'type': 'tree', 'summary': 'true'}
        assert 0 < kwargs['timeout'][1] <= 20
        return SimpleNamespace(raise_for_status=lambda: None, json=lambda: {
            'status': 'completed', 'result': [{
                'node_id': '0001', 'title': 'Nghỉ phép', 'page_index': 3, 'text': 'Nội dung gốc',
                'nodes': [{'node_id': '0002', 'title': 'Chi tiết', 'text': 'Chi tiết gốc'}],
            }],
        })

    monkeypatch.setattr(pageindex.requests, 'get', get)
    monkeypatch.setattr(pageindex, 'call_llm', lambda *args: '["fake-id", "pageindex:pi-123:0002", "pageindex:pi-123:0002", "pageindex:pi-123:0001"]')
    output = pageindex.pageindex_search('nghỉ phép', top_k=2)
    validate_search_results(output, top_k=2, expected_method='pageindex')
    assert [item['content'] for item in output] == ['Chi tiết gốc', 'Nội dung gốc']
    assert output[1]['metadata']['page_index'] == 3
    assert output[0]['metadata']['source'] == 'law.docx'


@pytest.mark.parametrize('mode', ['pending', 'timeout', 'stale'])
def test_pageindex_unavailable_returns_empty(pageindex_cache, monkeypatch, mode):
    document, _ = pageindex_cache
    if mode == 'stale':
        document['content'] = 'changed'

    def get(*args, **kwargs):
        if mode == 'stale':
            pytest.fail('Stale cache used')
        if mode == 'timeout':
            raise requests.Timeout()
        return SimpleNamespace(raise_for_status=lambda: None, json=lambda: {'status': 'processing'})

    monkeypatch.setattr(pageindex.requests, 'get', get)
    monkeypatch.setattr(pageindex, 'call_llm', lambda *args: pytest.fail('LLM called without nodes'))
    assert pageindex.pageindex_search('lao động') == []


def test_generation_preserves_citation_mapping_after_reorder(monkeypatch):
    chunks = [result(str(i), 1 - i / 10, 'hybrid') for i in range(4)]
    monkeypatch.setattr(generation, 'retrieve', lambda *args, **kwargs: chunks)

    def answer(system, user):
        context = json.loads(user)['context']
        assert context.index('[Source 1') < context.index('[Source 3') < context.index('[Source 4') < context.index('[Source 2')
        assert '[Source 2 | ID: 1' in context
        return 'Thông tin từ nguồn thứ hai. [2]'

    monkeypatch.setattr(generation, 'call_llm', answer)
    output = generation.generate_with_citation('nghỉ phép')
    validate_generation_result(output)
    assert output['sources'] == chunks
    assert all('citation_number' not in chunk for chunk in chunks)
    assert output['retrieval_source'] == 'hybrid'


@pytest.mark.parametrize('answer', ['No citation', 'Sai nguồn [0]', 'Sai nguồn [2]', generation.REFUSAL])
def test_generation_rejects_bad_citations(monkeypatch, answer):
    monkeypatch.setattr(generation, 'retrieve', lambda *args, **kwargs: [result()])
    monkeypatch.setattr(generation, 'call_llm', lambda *args: answer)
    output = generation.generate_with_citation('query')
    validate_generation_result(output)
    assert output['retrieval_source'] == 'none'
    assert output['sources'] == []


@pytest.mark.parametrize('stage', ['retrieval', 'llm', 'empty'])
def test_generation_failure_is_safe(monkeypatch, stage):
    def retrieve(*args, **kwargs):
        if stage == 'retrieval':
            raise requests.Timeout()
        return [] if stage == 'empty' else [result()]

    def fail(*args):
        if stage == 'empty':
            pytest.fail('LLM should not run')
        raise requests.Timeout()

    monkeypatch.setattr(generation, 'retrieve', retrieve)
    monkeypatch.setattr(generation, 'call_llm', fail)
    assert generation.generate_with_citation('query')['answer'] == generation.REFUSAL


def test_openrouter_chat_request(monkeypatch):
    monkeypatch.setenv('LLM_PROVIDER', 'openrouter')
    monkeypatch.setenv('LLM_MODEL', 'test-model')
    monkeypatch.setenv('OPENROUTER_API_KEY', 'test-key')

    def post(url, **kwargs):
        assert url == 'https://openrouter.ai/api/v1/chat/completions'
        assert kwargs['json']['model'] == 'test-model'
        assert kwargs['json']['messages'][0]['role'] == 'system'
        assert kwargs['timeout'] == (10, 120)
        return SimpleNamespace(raise_for_status=lambda: None, json=lambda: {
            'choices': [{'finish_reason': 'stop', 'message': {'content': 'answer'}}],
        })

    monkeypatch.setattr(llm.requests, 'post', post)
    assert llm.call_llm('system', 'user') == 'answer'
