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


def test_first_answer_gets_complete_list_and_deduplicated_sources(monkeypatch):
    article = ('**Điều 35. Chấm dứt hợp đồng**\n\n'
               '2. Không cần báo trước:\n\na) First case.\n\nb) Second case.\n\nc) Third case.\n\nd) Fourth case.')
    document = {'id': 'legal/law.md', 'content': article + '\n\n**Điều 36. Next**\n\nNext article.'}
    monkeypatch.setattr(context, 'load_documents', lambda: [document])
    chunks = [hit(0, 'a) First case.'), hit(1, 'b) Second case.')]
    monkeypatch.setattr(generation, 'retrieve', lambda *args, **kwargs: chunks)
    calls = []

    def llm(system, user):
        calls.append(system)
        assert system == generation.SYSTEM_PROMPT
        payload = json.loads(user)
        assert article in payload['context']
        assert payload['context'].count('[Source ') == 1
        assert 'Next article.' not in payload['context']
        return 'All four cases are available [1].'

    monkeypatch.setattr(generation, 'call_llm', llm)
    result = generation.generate_with_citation('List all cases')
    validate_generation_result(result)
    assert len(calls) == 1
    assert len(result['sources']) == 1
    assert result['sources'][0]['content'] == article
    assert result['sources'][0]['id'] == chunks[0]['id']


def test_context_budget_skips_whole_sources_and_keeps_citation_mapping(monkeypatch):
    chunks = [hit(0, 'First.'), hit(1, 'x' * 1000), hit(2, 'Last.')]
    monkeypatch.setattr(generation, 'expand_legal_articles', lambda items: items)
    monkeypatch.setattr(generation, 'MAX_CONTEXT_CHARS', len(generation.format_context([chunks[0], chunks[2]])))
    monkeypatch.setattr(generation, 'retrieve', lambda *args, **kwargs: chunks)

    def llm(system, user):
        prompt = json.loads(user)['context']
        assert len(prompt) <= generation.MAX_CONTEXT_CHARS
        assert '[Source 2 | ID: legal/law.md::chunk-2' in prompt
        assert 'x' * 100 not in prompt
        return 'Final source [2].'

    monkeypatch.setattr(generation, 'call_llm', llm)
    result = generation.generate_with_citation('query')
    validate_generation_result(result)
    assert result['sources'] == [chunks[0], chunks[2]]
    assert result['answer'] == 'Final source [2].'


def test_no_model_call_when_no_source_fits_context_budget(monkeypatch):
    monkeypatch.setattr(generation, 'expand_legal_articles', lambda items: items)
    monkeypatch.setattr(generation, 'MAX_CONTEXT_CHARS', 1)
    monkeypatch.setattr(generation, 'retrieve', lambda *args, **kwargs: [hit()])
    monkeypatch.setattr(generation, 'call_llm', lambda *args: pytest.fail('No context available'))
    assert generation.generate_with_citation('query')['sources'] == []


def test_identical_articles_in_different_documents_are_not_deduplicated(monkeypatch):
    article = '**Điều 35. Title**\n\nMatching passage.'
    monkeypatch.setattr(context, 'load_documents', lambda: [
        {'id': doc, 'content': article} for doc in ['legal/law.md', 'legal/other.md']])
    result = context.expand_legal_articles([hit(), hit(doc='legal/other.md')])
    assert len(result) == 2
    assert all(item['content'] == article for item in result)
