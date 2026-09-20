# Individual contribution report

Mỗi thành viên copy template này thành:

```text
reports/<student-id>-<short-name>.md
```

Giới hạn khuyến nghị: 1 trang, không chép lại README hoặc mô tả lý thuyết chung. Báo cáo không phải một bài pipeline cá nhân; mục đích là ghi nhận ownership và bằng chứng đóng góp trong sản phẩm nhóm.

---

## Thông tin

- Họ và tên: Nguyễn Thế Khang
- Mã học viên: 2A202602964
- Nhóm: DKH
- Repository/branch: https://github.com/ai-dnn/K4-L3A-RAG-Pipeline/tree/ngkhang

## Phần việc đã thực hiện

| Module/deliverable | Việc tôi trực tiếp làm | File/commit/PR | Trạng thái |
|---|---|---|---|
| Data collection (Task 1–3) | Thu thập 4 văn bản pháp luật, crawl 5 bài tin tức, chuyển đổi Markdown | `src/task1–3`, `data/` | Done |
| Chunking & Indexing (Task 4) | Cấu hình chunk_size=500, embedding bge-m3 qua OpenRouter, upsert ChromaDB | `src/task4_chunking_indexing.py` | Done |
| Search & Reranking (Task 5–7) | Semantic search, BM25 lexical search, RRF fusion k=60 | `src/task5–7` | Done |
| Fallback & Pipeline (Task 8–9) | PageIndex fallback, calibrate threshold 0.5978 | `src/task8–9` | Done |
| Generation (Task 10) | Prompt tiếng Việt, citation mapping, safe refusal | `src/task10_generation.py`, `src/llm.py` | Done |
| Streamlit UI | Integrate RAG pipeline, hiển thị sources/scores | `app.py` | Done |
| Evaluation | Golden dataset 19 Q&A, RESULT.md, run_evaluation.py | `group_project/evaluation/`, `run_evaluation.py` | Done |

Chỉ kê khai công việc có thể đối chiếu bằng file, commit, pull request, test hoặc kết quả evaluation.

## Quyết định kỹ thuật quan trọng

Mô tả tối đa hai quyết định mà bạn trực tiếp tham gia:

1. **Quyết định:** Dùng OpenRouter API cho cả embedding (bge-m3) và generation (gemini-2.5-flash) thay vì chạy local.  
   **Lý do/evidence:** Tránh yêu cầu GPU, giảm thời gian setup, embedding dimension 1024 cho kết quả tốt trên tiếng Việt.  
   **Trade-off:** Phụ thuộc vào kết nối mạng và API key; nhưng có fallback `sentence_transformers` local cho embedding.

2. **Quyết định:** Dùng cosine score gốc của dense search (không phải RRF score) để quyết định fallback sang PageIndex.  
   **Lý do/evidence:** RRF score là rank-based, không phản ánh semantic relevance thực tế; cosine score trực tiếp đo similarity.  
   **Trade-off:** Threshold cần calibrate riêng cho mỗi corpus; 0.5978 chỉ dựa trên 8 queries thử nghiệm.

## Kiểm thử và kết quả

- Test đã dùng: `pytest tests/test_contracts.py -q` → 15/15 passed
- Kết quả trước/sau: Hybrid+RRF cải thiện context recall +7.06% so với dense-only
- Lỗi đã phát hiện: BM25 IDF âm khi corpus nhỏ → sửa bằng Lucene IDF formula (`math.log1p`)

## Điều còn hạn chế

- Một hạn chế cụ thể: Threshold fallback chỉ được calibrate trên 8 queries, chưa tối ưu cho toàn bộ golden dataset.
- Nếu có thêm thời gian, thay đổi đầu tiên: Tăng chunk_size lên 800–1000 cho văn bản pháp luật dài, và chạy threshold sweep trên golden dataset.

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc của mình và có thể giải thích hoặc chạy lại trong buổi demo.

- Ngày: 2026-09-20
- Tên thành viên: Nguyễn Thế Khang
