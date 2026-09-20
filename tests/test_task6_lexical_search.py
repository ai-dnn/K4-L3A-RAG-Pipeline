from types import SimpleNamespace
import unicodedata

import pytest

from src import task6_lexical_search as lexical
from src.contracts import validate_search_results


def chunk(item_id, content):
    return {'id': item_id, 'content': content, 'metadata': {
        'source': 'law.docx', 'title': 'Bộ luật Lao động', 'doc_type': 'legal',
        'url': '', 'chunk_index': 0,
    }}


@pytest.mark.parametrize('query,top_k', [('', 3), ('?!', 3), ('lao động', 0), ('lao động', -1)])
def test_invalid_query_skips_database(monkeypatch, query, top_k):
    monkeypatch.setattr(lexical, 'get_collection', lambda: pytest.fail('Unexpected database access'))
    assert lexical.lexical_search(query, top_k) == []


def test_empty_corpus(monkeypatch):
    monkeypatch.setattr(lexical, 'CORPUS', [])
    monkeypatch.setattr(lexical, 'get_collection', lambda: SimpleNamespace(
        get=lambda **kwargs: {'ids': [], 'documents': [], 'metadatas': []},
    ))
    assert lexical.lexical_search('lao động') == []
    assert lexical.build_bm25_index([chunk('a', '?!')]) is None


def test_repeated_terms_do_not_grow_scores_linearly():
    index = lexical.build_bm25_index([chunk('a', 'nghỉ'), chunk('b', 'nghỉ ' * 100)])
    scores = index.get_scores(['nghỉ'])
    assert 0 < scores[1] < 4 * scores[0]


def test_single_document_unicode_and_no_match(monkeypatch):
    corpus = [chunk('a', 'Điều 113. Nghỉ hằng năm')]
    monkeypatch.setattr(lexical, 'CORPUS', corpus)
    query = unicodedata.normalize('NFD', 'NGHỈ, HẰNG NĂM!')
    results = lexical.lexical_search(query)
    validate_search_results(results, top_k=10, expected_method='bm25')
    assert results[0]['id'] == 'a'
    assert results[0]['score'] > 0
    assert results[0]['metadata']['url'] is None
    assert corpus[0]['metadata']['url'] == ''
    assert lexical.lexical_search('xyzunknown') == []


def test_reads_indexed_chunks_and_limits_results(monkeypatch):
    corpus = [chunk('b', 'Điều 113 nghỉ hằng năm'), chunk('a', 'Điều 113 nghỉ hằng năm'),
              chunk('c', 'Hợp đồng lao động')]
    monkeypatch.setattr(lexical, 'CORPUS', [])

    def get(**kwargs):
        assert kwargs['include'] == ['documents', 'metadatas']
        return {'ids': [item['id'] for item in corpus],
                'documents': [item['content'] for item in corpus],
                'metadatas': [item['metadata'] for item in corpus]}

    monkeypatch.setattr(lexical, 'get_collection', lambda: SimpleNamespace(get=get))
    results = lexical.lexical_search('113', top_k=1)
    validate_search_results(results, top_k=1, expected_method='bm25')
    assert results[0]['id'] == 'a'
    assert results[0]['content'] == corpus[1]['content']
