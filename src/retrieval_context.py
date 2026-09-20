"""Expand legal search hits to the articles surrounding their exact text."""

import re

from .task4_chunking_indexing import load_documents

ARTICLE = re.compile(r'(?m)^(?:\*\*)?Điều\s+\d+[a-z]?\.')
MAX_ARTICLE_CHARS = 12000


def expand_legal_articles(chunks: list[dict]) -> list[dict]:
    eligible = [item for item in chunks if item['metadata'].get('doc_type') == 'legal'
                and '::chunk-' in item['id']]
    if not eligible:
        return chunks
    documents = {item['id']: item for item in load_documents()}
    expanded, seen_articles = [], set()
    for item in chunks:
        document = documents.get(item['id'].split('::chunk-')[0]) if item in eligible else None
        text = document['content'] if document else ''
        content = item['content']
        start = text.find(content)
        # Do not guess when the index no longer matches, or the text is ambiguous.
        if start >= 0 and text.find(content, start + 1) == -1:
            boundaries = [match.start() for match in ARTICLE.finditer(text)]
            before = [position for position in boundaries if position <= start]
            after = [position for position in boundaries if position >= start + len(content)]
            if before:
                article = text[before[-1]:after[0] if after else len(text)].strip()
                if len(article) <= MAX_ARTICLE_CHARS:
                    identity = (document['id'], before[-1], after[0] if after else len(text))
                    if identity in seen_articles:
                        continue
                    seen_articles.add(identity)
                    content = article
        expanded.append({**item, 'content': content})
    return expanded
