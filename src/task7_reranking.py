"""Task 7 — Reciprocal Rank Fusion; không dùng RRF score làm cosine score."""


def rerank_rrf(ranked_lists: list[list[dict]], top_k: int = 5, k: int = 60) -> list[dict]:
    """Gộp theo ID, mỗi tài liệu chỉ đóng góp một lần trong mỗi bảng xếp hạng."""
    if top_k <= 0:
        return []
    if k < 0:
        raise ValueError("k must be non-negative")
    scores, items = {}, {}
    for ranked_list in ranked_lists:
        seen = set()
        for rank, item in enumerate(ranked_list, 1):
            item_id = item['id']
            if item_id in seen:
                continue
            seen.add(item_id)
            scores[item_id] = scores.get(item_id, 0.0) + 1 / (k + rank)
            items.setdefault(item_id, item)
    ranked_ids = sorted(scores, key=lambda item_id: (-scores[item_id], item_id))
    return [{**items[item_id], 'score': scores[item_id], 'retrieval_method': 'hybrid'}
            for item_id in ranked_ids[:top_k]]


if __name__ == '__main__':
    from .task5_semantic_search import semantic_search
    from .task6_lexical_search import lexical_search

    query = 'Người lao động được nghỉ hằng năm bao nhiêu ngày?'
    for result in rerank_rrf([semantic_search(query), lexical_search(query)], top_k=3):
        print(result)
