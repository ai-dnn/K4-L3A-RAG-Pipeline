from types import SimpleNamespace

import pytest

from src import task4_chunking_indexing as indexing


def test_docx_replaces_matching_pdf_without_ocr(tmp_path, monkeypatch):
    from src import task3_convert_markdown as conversion

    landing = tmp_path / 'landing'
    (landing / 'legal').mkdir(parents=True)
    docx, stem = next(iter(conversion.LEGAL_ALIASES.items()))
    (landing / 'legal' / docx).touch()
    (landing / 'legal' / f'{stem}.pdf').touch()
    calls = []

    def convert(path):
        calls.append(path)
        return SimpleNamespace(text_content='Điều 1. Phạm vi điều chỉnh')

    monkeypatch.setattr(conversion, 'LANDING_DIR', landing)
    monkeypatch.setattr(conversion, 'OUTPUT_DIR', tmp_path / 'standardized')
    monkeypatch.setattr(conversion, 'MarkItDown', lambda: SimpleNamespace(convert=convert))
    monkeypatch.setattr(conversion, 'ocr_pdf', lambda path: pytest.fail('DOCX must not use OCR'))
    conversion.convert_legal_docs()
    conversion.convert_legal_docs()
    outputs = list((tmp_path / 'standardized/legal').glob('*.md'))
    assert [path.name for path in outputs] == [f'{stem}.md']
    assert all(path.endswith(docx) for path in calls)
    assert f'**Source:** {docx}' in outputs[0].read_text(encoding='utf-8')


def test_loading_metadata_and_stable_chunks(tmp_path, monkeypatch):
    for folder in ('legal', 'news'):
        (tmp_path / folder).mkdir()
    (tmp_path / 'legal/law.md').write_text(
        '# Bộ luật Lao động\n\n**Source:** local.docx\n\n---\n\n' + 'Điều 1. Lao động. ' * 100,
        encoding='utf-8',
    )
    (tmp_path / 'news/article.md').write_text(
        '# Tin lao động\n\n**Source:** https://example.org/article\n\n---\n\nNội dung bài viết',
        encoding='utf-8',
    )
    (tmp_path / 'legal/empty.md').write_text('  ')
    monkeypatch.setattr(indexing, 'STANDARDIZED_DIR', tmp_path)
    documents = indexing.load_documents()
    assert len(documents) == 2
    assert documents[0]['metadata'] == {
        'title': 'Bộ luật Lao động', 'source': 'local.docx', 'doc_type': 'legal', 'url': None,
    }
    assert documents[1]['metadata']['url'] == 'https://example.org/article'
    chunks = indexing.chunk_documents(documents)
    assert chunks == indexing.chunk_documents(indexing.load_documents())
    assert len({chunk['id'] for chunk in chunks}) == len(chunks)
    assert all(0 < len(chunk['content']) <= indexing.CHUNK_SIZE for chunk in chunks)
    assert indexing.chunk_documents([]) == []


def test_embed_texts_batches_and_normalizes(monkeypatch):
    monkeypatch.setattr(indexing, 'EMBEDDING_PROVIDER', 'sentence_transformers')
    calls = []

    def encode(texts, **kwargs):
        calls.append((texts, kwargs))
        return SimpleNamespace(tolist=lambda: [[1.0, 0.0] for _ in texts])

    monkeypatch.setattr(indexing, '_get_model', lambda: SimpleNamespace(encode=encode))
    assert indexing.embed_texts([]) == []
    assert not calls
    assert indexing.embed_texts(['a', 'b']) == [[1.0, 0.0], [1.0, 0.0]]
    assert calls[0][1]['batch_size'] == 32
    assert calls[0][1]['normalize_embeddings'] is True


def test_embedding_alignment_and_input_preservation(monkeypatch):
    chunks = [{'id': 'a', 'content': 'first'}, {'id': 'b', 'content': 'second'}]
    monkeypatch.setattr(indexing, 'embed_texts', lambda texts: [[1.0], [2.0]])
    embedded = indexing.embed_chunks(chunks)
    assert [chunk['embedding'] for chunk in embedded] == [[1.0], [2.0]]
    assert all('embedding' not in chunk for chunk in chunks)
    monkeypatch.setattr(indexing, 'embed_texts', lambda texts: [])
    with pytest.raises(ValueError, match='count'):
        indexing.embed_chunks(chunks)


def test_chroma_persists_upserts_without_duplicates(tmp_path, monkeypatch):
    monkeypatch.setattr(indexing, 'CHROMA_DIR', tmp_path / 'chroma')
    chunk = {
        'id': 'legal/law.md::chunk-0', 'content': 'Vietnamese labor law',
        'embedding': [1.0, 0.0, 0.0],
        'metadata': {'source': 'local.docx', 'title': 'Labor law',
                     'doc_type': 'legal', 'url': None, 'chunk_index': 0},
    }
    indexing.index_to_vectorstore([chunk])
    indexing.index_to_vectorstore([{**chunk, 'content': 'Updated labor law'}])
    collection = indexing.get_collection()
    assert collection.count() == 1
    stored = collection.get(include=['documents', 'metadatas'])
    assert stored['documents'] == ['Updated labor law']
    assert stored['metadatas'][0]['url'] == ''
    assert chunk['metadata']['url'] is None
    query = collection.query(query_embeddings=[[1.0, 0.0, 0.0]], n_results=1)
    assert query['distances'][0][0] == pytest.approx(0.0)
    assert (tmp_path / 'chroma/chroma.sqlite3').exists()
    monkeypatch.setattr(indexing, 'EMBEDDING_MODEL', 'different-model')
    with pytest.raises(ValueError, match='configuration'):
        indexing.get_collection()


def test_openrouter_batches_orders_and_normalizes(monkeypatch):
    monkeypatch.setattr(indexing, 'EMBEDDING_PROVIDER', 'openrouter')
    monkeypatch.setenv('OPENROUTER_API_KEY', 'test-key')
    calls = []

    def post(url, **kwargs):
        assert url == 'https://openrouter.ai/api/v1/embeddings'
        assert kwargs['headers']['Authorization'] == 'Bearer test-key'
        assert kwargs['json']['model'] == indexing.EMBEDDING_MODEL
        batch = kwargs['json']['input']
        calls.append(batch)
        data = []
        for index, text in enumerate(batch):
            vector = [0.0] * indexing.EMBEDDING_DIM
            vector[int(text)] = 2.0
            data.append({'index': index, 'embedding': vector})
        return SimpleNamespace(raise_for_status=lambda: None, json=lambda: {'data': data[::-1]})

    monkeypatch.setattr(indexing.requests, 'post', post)
    vectors = indexing.embed_texts([str(i) for i in range(33)])
    assert [len(batch) for batch in calls] == [32, 1]
    assert len(vectors) == 33
    assert all(vector[index] == 1.0 for index, vector in enumerate(vectors))


def test_openrouter_missing_key_and_invalid_response(monkeypatch):
    monkeypatch.setattr(indexing, 'EMBEDDING_PROVIDER', 'openrouter')
    monkeypatch.delenv('OPENROUTER_API_KEY', raising=False)
    with pytest.raises(ValueError, match='OPENROUTER_API_KEY'):
        indexing.embed_texts(['test'])
    monkeypatch.setenv('OPENROUTER_API_KEY', 'test-key')
    monkeypatch.setattr(indexing.requests, 'post', lambda *args, **kwargs: SimpleNamespace(
        raise_for_status=lambda: None, json=lambda: {'data': []},
    ))
    with pytest.raises(ValueError, match='indices'):
        indexing.embed_texts(['test'])
