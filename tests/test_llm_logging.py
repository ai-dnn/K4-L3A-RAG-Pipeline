import json
from types import SimpleNamespace

import pytest
import requests

from src import llm, llm_logging


@pytest.fixture
def log_file(tmp_path, monkeypatch):
    path = tmp_path / 'llm.log'
    monkeypatch.setattr(llm_logging, 'LOG_PATH', path)
    monkeypatch.setattr(llm_logging._logger, 'handlers', [])
    monkeypatch.setenv('LLM_PROVIDER', 'openrouter')
    monkeypatch.setenv('OPENROUTER_API_KEY', 'private-test-api-key')
    monkeypatch.delenv('LLM_LOG_CONTENT', raising=False)
    yield path
    for handler in llm_logging._logger.handlers:
        handler.close()


def response():
    return SimpleNamespace(raise_for_status=lambda: None, json=lambda: {
        'id': 'test-response', 'usage': {'prompt_tokens': 12, 'completion_tokens': 4},
        'choices': [{'finish_reason': 'stop', 'message': {'content': 'private answer'}}],
    })


def test_metadata_and_no_content_by_default(log_file, monkeypatch):
    monkeypatch.setattr(llm.requests, 'post', lambda *args, **kwargs: response())
    assert llm.call_llm('private system', 'private question') == 'private answer'
    records = [json.loads(line) for line in log_file.read_text().splitlines()]
    assert [r['event'] for r in records] == ['llm.request', 'llm.response']
    assert records[0]['request_id'] == records[1]['request_id']
    assert records[1]['usage']['prompt_tokens'] == 12
    assert records[1]['elapsed_ms'] >= 0
    assert 'private' not in log_file.read_text()


def test_content_opt_in_redacts_keys(log_file, monkeypatch):
    monkeypatch.setenv('LLM_LOG_CONTENT', 'true')
    monkeypatch.setattr(llm.requests, 'post', lambda *args, **kwargs: response())
    llm.call_llm('system', 'question private-test-api-key')
    records = [json.loads(line) for line in log_file.read_text().splitlines()]
    assert records[0]['user_message'] == 'question [REDACTED]'
    assert records[1]['answer'] == 'private answer'
    assert 'private-test-api-key' not in log_file.read_text()


def test_http_errors_are_logged_and_reraised(log_file, monkeypatch):
    def fail(*args, **kwargs):
        response = requests.Response()
        response.status_code = 429
        raise requests.HTTPError('private error body', response=response)
    monkeypatch.setattr(llm.requests, 'post', fail)
    with pytest.raises(requests.HTTPError):
        llm.call_llm('system', 'user')
    records = [json.loads(line) for line in log_file.read_text().splitlines()]
    assert records[-1]['event'] == 'llm.error'
    assert records[-1]['status_code'] == 429
    assert records[-1]['error_type'] == 'HTTPError'
    assert 'private error body' not in log_file.read_text()
