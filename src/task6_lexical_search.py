"""Task 6 — BM25 trên cùng corpus chunks trong Chroma với Task 5."""

import re
import math
import unicodedata

from rank_bm25 import BM25Okapi

from .task4_chunking_indexing import get_collection


CORPUS: list[dict] = []


class _BM25(BM25Okapi):
    def _calc_idf(self, document_frequencies):
        # Lucene IDF: luôn dương, kể cả corpus chỉ có một/hai tài liệu.
        self.idf = {
            term: math.log1p((self.corpus_size - count + 0.5) / (count + 0.5))
            for term, count in document_frequencies.items()
        }


def _tokenize(text: str) -> list[str]:
    return re.findall(r"\w+", unicodedata.normalize("NFC", text).casefold())


def build_bm25_index(corpus: list[dict]):
    """BM25 có term-frequency saturation và IDF dương cho corpus nhỏ."""
    tokenized = [_tokenize(item["content"]) for item in corpus]
    return _BM25(tokenized) if any(tokenized) else None


def lexical_search(query: str, top_k: int = 10) -> list[dict]:
    """Trả về BM25 SearchResult theo score giảm dần."""
    tokens = _tokenize(query)
    if not tokens or top_k <= 0:
        return []
    corpus = CORPUS
    if not corpus:
        stored = get_collection().get(include=["documents", "metadatas"])
        corpus = [
            {"id": item_id, "content": content, "metadata": metadata}
            for item_id, content, metadata in zip(
                stored["ids"], stored["documents"], stored["metadatas"],
            )
        ]
    bm25 = build_bm25_index(corpus)
    if bm25 is None:
        return []
    scores = bm25.get_scores(tokens)
    indices = sorted(range(len(corpus)), key=lambda index: (-scores[index], corpus[index]["id"]))
    results = []
    for index in indices[:top_k]:
        if scores[index] <= 0:
            continue
        item = corpus[index]
        results.append({
            "id": item["id"],
            "content": item["content"],
            "score": float(scores[index]),
            "metadata": {**item["metadata"], "url": item["metadata"].get("url") or None},
            "retrieval_method": "bm25",
        })
    return results


if __name__ == "__main__":
    for result in lexical_search("Điều 113 nghỉ hằng năm", top_k=3):
        print(result)
