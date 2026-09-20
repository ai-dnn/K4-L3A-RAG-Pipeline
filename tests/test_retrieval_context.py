import copy
import json

import pytest

from src import retrieval_context as context
from src import task10_generation as generation
from src.contracts import validate_generation_result


def hit(index=0, content='Matching passage.', doc='legal/law.md'):
    return {'id': f'{doc}::chunk-{index}', 'content': content, 'score': 1 / (index + 1),
            'metadata': {'source': doc, 'title': 'Law', 'doc_type': doc.split('/')[0],
                         'chunk_index': index, 'url': None}, 'retrieval_method': 'hybrid'}


def test_expand_article_keeps_heading_and_remaining_clauses(monkeypatch):
    article = '**Điều 36. Title**\n\nMatching passage.\n\nAnother clause.'
    monkeypatch.setattr(context, 'load_documents', lambda: [
        {'id': 'legal/law.md', 'content': '**Điều 35. Before**\n\nBefore.\n\n' + article + '\n\n**Điều 37. After**\n\nAfter.'}])
    chunks = [hit()]
    original = copy.deepcopy(chunks)
    output = context.expand_legal_articles(chunks)
    assert output[0]['content'] == article
    assert output[0]['id'] == chunks[0]['id']
    assert chunks == original


@pytest.mark.parametrize('text', [
    '**Điều 36. Title**\n\nChanged passage.',
    '**Điều 36. Title**\n\nMatching passage. Matching passage.',
    '**Điều 36. Title**\n\nMatching passage.' + 'x' * context.MAX_ARTICLE_CHARS,
])
def test_expansion_does_not_guess_or_silently_truncate(monkeypatch, text):
    monkeypatch.setattr(context, 'load_documents', lambda: [{'id': 'legal/law.md', 'content': text}])
    assert context.expand_legal_articles([hit()]) == [hit()]


def test_news_does_not_load_legal_documents(monkeypatch):
    monkeypatch.setattr(context, 'load_documents', lambda: pytest.fail('Unexpected document load'))
    chunks = [hit(doc='news/article.md')]
    assert context.expand_legal_articles(chunks) == chunks


def test_retry_uses_original_question_and_preserves_source_mapping(monkeypatch):
    original, first, second = hit(), hit(1, 'First meaning.'), hit(2, 'Second meaning.')
    searches = []
    calls = []
    monkeypatch.setattr(generation, 'expand_legal_articles', lambda items: items)

    def retrieve(query, top_k):
        searches.append(query)
        return {'original': [original], 'first': [first], 'second': [second]}[query]

    def llm(system, user):
        calls.append(system)
        payload = json.loads(user)
        assert payload['question'] == 'original'
        if system == generation.REWRITE_PROMPT:
            return '["first", "second"]'
        if len(calls) == 1:
            return generation.REFUSAL
        assert '[Source 2 | ID: legal/law.md::chunk-1' in payload['context']
        assert 'Second meaning.' in payload['context']
        return 'Grounded response [2].'

    monkeypatch.setattr(generation, 'retrieve', retrieve)
    monkeypatch.setattr(generation, 'call_llm', llm)
    result = generation.generate_with_citation('original', top_k=3)
    validate_generation_result(result)
    assert searches == ['original', 'first', 'second']
    assert result['sources'][1] == first
    assert len(calls) == 3


def test_retry_stops_after_second_refusal(monkeypatch):
    calls = []
    monkeypatch.setattr(generation, 'expand_legal_articles', lambda items: items)
    monkeypatch.setattr(generation, 'retrieve', lambda *args, **kwargs: [hit()])

    def llm(system, user):
        calls.append(system)
        return '["rewrite"]' if system == generation.REWRITE_PROMPT else generation.REFUSAL

    monkeypatch.setattr(generation, 'call_llm', llm)
    assert generation.generate_with_citation('query')['sources'] == []
    assert len(calls) == 3


@pytest.mark.parametrize('rewrites', ['[]', 'not json', '{}', '[null, 42]', '["query", "query"]'])
def test_invalid_or_out_of_domain_rewrites_do_not_search(monkeypatch, rewrites):
    monkeypatch.setattr(generation, 'call_llm', lambda *args: rewrites)
    monkeypatch.setattr(generation, 'retrieve', lambda *args, **kwargs: pytest.fail('Unexpected search'))
    assert generation.retry_retrieval('query', [hit()], 5) == []
