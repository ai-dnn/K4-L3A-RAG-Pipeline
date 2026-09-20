"""OpenRouter chat dùng chung cho chọn PageIndex nodes và generation."""

import os
from time import perf_counter
from uuid import uuid4

import requests
from dotenv import load_dotenv

from .llm_logging import log_event

load_dotenv()


def call_llm(system_prompt: str, user_message: str) -> str:
    request_id = uuid4().hex[:12]
    started = perf_counter()
    model = os.getenv('LLM_MODEL') or 'google/gemini-2.5-flash'
    provider = os.getenv('LLM_PROVIDER') or 'openrouter'
    include_content = os.getenv('LLM_LOG_CONTENT', '').lower() == 'true'
    log_event('llm.request', request_id=request_id, provider=provider, model=model,
              system_chars=len(system_prompt), user_chars=len(user_message),
              **({'system_prompt': system_prompt, 'user_message': user_message} if include_content else {}))
    try:
        return _request(system_prompt, user_message, model, provider, request_id, started, include_content)
    except Exception as error:
        response = getattr(error, 'response', None)
        log_event('llm.error', request_id=request_id, model=model,
                  elapsed_ms=round((perf_counter() - started) * 1000),
                  error_type=type(error).__name__,
                  status_code=getattr(response, 'status_code', None))
        raise


def _request(system_prompt, user_message, model, provider, request_id, started, include_content):
    if provider != 'openrouter':
        raise ValueError('Set LLM_PROVIDER=openrouter')
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        raise ValueError('Set OPENROUTER_API_KEY in .env')
    response = requests.post(
        'https://openrouter.ai/api/v1/chat/completions',
        headers={'Authorization': f'Bearer {api_key}'},
        json={
            'model': model,
            'messages': [{'role': 'system', 'content': system_prompt},
                         {'role': 'user', 'content': user_message}],
            'temperature': 0.3, 'top_p': 0.9, 'max_tokens': 4096,
        },
        timeout=(10, 120),
    )
    response.raise_for_status()
    data = response.json()
    choice = data['choices'][0]
    content = choice.get('message', {}).get('content')
    usage = data.get('usage') or {}
    log_event('llm.response', request_id=request_id, model=model,
              response_id=data.get('id'), elapsed_ms=round((perf_counter() - started) * 1000),
              finish_reason=choice.get('finish_reason'),
              usage={key: usage[key] for key in ('prompt_tokens', 'completion_tokens', 'total_tokens', 'cost') if key in usage},
              answer_chars=len(content) if isinstance(content, str) else 0,
              **({'answer': content} if include_content else {}))
    if choice.get('finish_reason') == 'length':
        raise ValueError('LLM response was truncated')
    if not isinstance(content, str) or not content.strip():
        raise ValueError('LLM returned no text')
    return content.strip()
