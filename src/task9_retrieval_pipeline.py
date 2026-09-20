"""Task 9 — Dense + BM25, RRF một lần, fallback dựa trên cosine gốc."""

import logging
import os

from dotenv import load_dotenv

from .task5_semantic_search import semantic_search
from .task6_lexical_search import lexical_search
from .task7_reranking import rerank_rrf
from .task8_pageindex_vectorless import pageindex_search

load_dotenv()
SCORE_THRESHOLD = float(os.getenv('SCORE_THRESHOLD') or '0.3')
DEFAULT_TOP_K = 5
logger = logging.getLogger(__name__)


def retrieve(query: str, top_k: int = DEFAULT_TOP_K,
             score_threshold: float = SCORE_THRESHOLD, use_reranking: bool = True) -> list[dict]:
    """Giữ hybrid/dense results nếu PageIndex không có kết quả hoặc bị lỗi."""
    if not query.strip() or top_k <= 0:
        return []
    dense = semantic_search(query, top_k=top_k * 2)
    if use_reranking:
        sparse = lexical_search(query, top_k=top_k * 2)
        results = rerank_rrf([dense, sparse], top_k=top_k)
    else:
        results = dense[:top_k]
    best_dense_score = max((item['score'] for item in dense), default=-1.0)
    if best_dense_score < score_threshold:
        try:
            fallback = pageindex_search(query, top_k=top_k)
            if fallback:
                return fallback[:top_k]
        except Exception as error:
            logger.warning('PageIndex unavailable (%s); keeping retrieval results', type(error).__name__)
    return results


if __name__ == '__main__':
    for result in retrieve('Người lao động được nghỉ hằng năm bao nhiêu ngày?', top_k=3):
        print(result)
