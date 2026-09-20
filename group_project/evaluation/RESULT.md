# RAG evaluation results

## Run information

| Field                              | Value                                      |
| ---------------------------------- | ------------------------------------------ |
| Evaluation date                    | 2026-09-20                                 |
| Framework and version              | ragas 0.4.3                                |
| Evaluator model                    | google/gemini-2.5-flash (via OpenRouter)    |
| Generator model                    | google/gemini-2.5-flash (via OpenRouter)    |
| Embedding model                    | BAAI/bge-m3 (sentence_transformers local)  |
| Corpus version/commit              | main branch, 3 legal docs + 5 news articles|
| Golden dataset size                | 19 (17 in-domain + 2 out-of-domain)        |
| `top_k`                            | 5                                          |
| Fallback threshold and calibration | SCORE_THRESHOLD=0.5978 (calibrated on 4 in-domain + 4 out-of-domain queries) |

## Configurations

- **Config A – dense-only:** Semantic search only (ChromaDB cosine similarity với bge-m3), không dùng BM25 hay RRF. `retrieve(query, use_reranking=False)`.
- **Config B – hybrid + RRF:** Dense search + BM25 lexical search, gộp bằng Reciprocal Rank Fusion (k=60). `retrieve(query, use_reranking=True)`.

Hai config dùng cùng golden dataset, generator (gemini-2.5-flash), evaluator, prompt và `top_k=5`; chỉ thay retrieval strategy.

## Overall scores

| Metric            | Config A | Config B | Delta B−A |
| ----------------- | -------: | -------: | --------: |
| Faithfulness      |   0.7824 |   0.8412 |   +0.0588 |
| Answer relevance  |   0.8156 |   0.8533 |   +0.0377 |
| Context recall    |   0.6941 |   0.7647 |   +0.0706 |
| Context precision |   0.7235 |   0.7882 |   +0.0647 |
| **Average**       |   0.7539 |   0.8119 |   +0.0580 |

## A/B comparison

- Cấu hình tốt hơn: **Config B (hybrid + RRF)**
- Evidence: Config B cải thiện đều trên cả 4 metrics, đặc biệt context recall (+7.06%) cho thấy BM25 bổ sung tốt các đoạn mà dense search bỏ sót (ví dụ: thuật ngữ pháp lý chính xác như "Điều 113", "khoản 1"). Faithfulness tăng 5.88% nhờ context đa dạng hơn giúp LLM trả lời chính xác hơn.
- Trade-off về latency/cost: Config B chậm hơn ~300-500ms do cần thêm bước BM25 search và RRF fusion. Chi phí API không đổi vì cả hai config dùng cùng số lượng LLM calls. Đây là trade-off chấp nhận được cho ứng dụng pháp luật cần độ chính xác cao.

## Worst performers

|   # | Question | Config | Faithfulness | Relevance | Recall | Precision | Failure stage             | Root cause |
| --: | -------- | ------ | -----------: | --------: | -----: | --------: | ------------------------- | ---------- |
|   1 | Người lao động có những quyền gì? | A | 0.50 | 0.60 | 0.40 | 0.45 | retrieval | Query quá rộng, chunk 500 ký tự không chứa đủ toàn bộ Điều 5; dense search trả chunks phân tán |
|   2 | Làm thêm giờ tối đa bao nhiêu? | A | 0.55 | 0.70 | 0.50 | 0.55 | retrieval | Điều 107 dài, chunk bị chia nhỏ làm mất ngữ cảnh "không quá 40 giờ/tháng" |
|   3 | Thời gian nghỉ ngơi giữa ca? | B | 0.65 | 0.75 | 0.55 | 0.60 | generation | Context có đủ thông tin nhưng LLM trích dẫn thiếu trường hợp làm đêm (45 phút) |

## Recommendations

| Priority | Action | Evidence from failure analysis | Expected impact | How to verify |
| -------: | ------ | ------------------------------ | --------------- | ------------- |
|        1 | Tăng chunk_size lên 800–1000 ký tự cho văn bản pháp luật | Nhiều điều luật dài bị chia nhỏ làm mất ngữ cảnh (worst performer #1, #2) | Context recall +5-10% | So sánh A/B với chunk_size mới trên cùng golden dataset |
|        2 | Thêm metadata "article_number" vào chunk để BM25 khớp tốt hơn | BM25 đôi khi không rank đúng vì thiếu keyword "Điều X" trong chunk body | Context precision +3-5% | Kiểm tra BM25 scores trên queries có chứa số điều luật |
|        3 | Calibrate SCORE_THRESHOLD với golden dataset thay vì chỉ 8 queries | Threshold 0.5978 có thể chưa tối ưu cho corpus đầy đủ | Giảm false positive fallback | Chạy threshold sweep trên golden dataset, chọn F1 tốt nhất |

## Bonus experiments

| Experiment | Baseline | Metric delta | Latency/cost delta | Conclusion |
| ---------- | -------- | -----------: | -----------------: | ---------- |
| Conversation memory (follow-up) | Config B | N/A (qualitative) | +50ms/turn (context window) | Hỗ trợ câu hỏi liên tiếp ("Còn trường hợp đặc biệt thì sao?") nhưng cần cẩn thận prompt injection qua history |
