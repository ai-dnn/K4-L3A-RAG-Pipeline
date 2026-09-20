"""OpenRouter chat dùng chung cho chọn PageIndex nodes và generation."""

import os

import requests
from dotenv import load_dotenv

load_dotenv()


def call_llm(system_prompt: str, user_message: str) -> str:
    provider = os.getenv('LLM_PROVIDER') or 'openrouter'
    if provider != 'openrouter':
        raise ValueError('Set LLM_PROVIDER=openrouter')
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        raise ValueError('Set OPENROUTER_API_KEY in .env')
    response = requests.post(
        'https://openrouter.ai/api/v1/chat/completions',
        headers={'Authorization': f'Bearer {api_key}'},
        json={
            'model': os.getenv('LLM_MODEL') or 'google/gemini-2.5-flash',
            'messages': [{'role': 'system', 'content': system_prompt},
                         {'role': 'user', 'content': user_message}],
            'temperature': 0.3, 'top_p': 0.9, 'max_tokens': 4096,
        },
        timeout=(10, 120),
    )
    response.raise_for_status()
    choice = response.json()['choices'][0]
    if choice.get('finish_reason') == 'length':
        raise ValueError('LLM response was truncated')
    content = choice['message']['content']
    if not isinstance(content, str) or not content.strip():
        raise ValueError('LLM returned no text')
    return content.strip()
