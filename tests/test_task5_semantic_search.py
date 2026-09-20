from types import SimpleNamespace

import pytest

from src import task5_semantic_search as semantic
from src.contracts import validate_search_results


@pytest.mark.parametrize('query,top_k', [('  ', 3), ('lao động', 0), ('lao động', -1)])
def test_empty_request_avoids_database_and_api(monkeypatch, query, top_k):
    monkeypatch.setattr(semantic, 'get_collection', lambda: pytest.fail('Unexpected database access'))
    monkeypatch.setattr(semantic, 'embed_texts', lambda texts: pytest.fail('Unexpected API call'))
    assert semantic.semantic_search(query, top_k) == []


def test_empty_collection_avoids_embedding(monkeypatch):
    monkeypatch.setattr(semantic, 'get_collection', lambda: SimpleNamespace(count=lambda: 0))
    monkeypatch.setattr(semantic, 'embed_texts', lambda texts: pytest.fail('Unexpected API call'))
    assert semantic.semantic_search('lao động') == []


def test_count_limit_cosine_order_and_source_metadata(monkeypatch):
    metadata = {'source': 'law.docx', 'title': 'Bộ luật Lao động',
                'doc_type': 'legal', 'url': '', 'chunk_index': 0}

    def embed(texts):
        assert texts == ['nghỉ phép']
        return [[1.0, 0.0]]

    def query(**kwargs):
        assert kwargs['n_results'] == 2
        assert kwargs['query_embeddings'] == [[1.0, 0.0]]
        return {'ids': [['a', 'b']], 'documents': [['Không liên quan', 'Nghỉ hằng năm']],
                'metadatas': [[metadata, {**metadata, 'chunk_index': 1}]],
                'distances': [[1.2, 0.1]]}

    monkeypatch.setattr(semantic, 'embed_texts', embed)
    monkeypatch.setattr(semantic, 'get_collection', lambda: SimpleNamespace(count=lambda: 2, query=query))
    results = semantic.semantic_search('nghỉ phép', top_k=10)
    validate_search_results(results, top_k=10, expected_method='dense')
    assert [item['id'] for item in results] == ['b', 'a']
    assert [item['score'] for item in results] == pytest.approx([0.9, -0.2])
    assert results[0]['metadata']['url'] is None
    assert results[0]['metadata']['source'] == 'law.docx'
    assert metadata['url'] == ''
