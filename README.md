# Day 8 — RAG Pipeline

## Mục tiêu

Mỗi nhóm xây dựng một chatbot RAG trả lời câu hỏi từ bộ tài liệu do nhóm thu thập. Sản phẩm phải có hybrid retrieval, citation, giao diện chat và báo cáo đánh giá.

Nhóm tự chọn bài toán và thu thập dữ liệu phù hợp; repo không cung cấp dữ liệu mẫu.

## Sản phẩm phải nộp

- Repository nhóm chạy được.
- Tối thiểu 3 tài liệu chính sách và 5 bài viết/page do nhóm tự thu thập.
- Pipeline: convert → chunk → index → dense + BM25 → RRF → fallback → generation có citation.
- Chatbot Streamlit hiển thị câu trả lời và nguồn đã dùng.
- Golden dataset tối thiểu 15 câu; đánh giá 4 metric và so sánh A/B.
- `group_project/evaluation/RESULT.md`.
- Mỗi thành viên nộp báo cáo cá nhân theo template trong `group_project/ịndividual/INDIVIDUAL_REPORT.md`.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e ".[dev]"
python -m playwright install chromium
cp .env.example .env
```

Điền API key cần dùng trong `.env`; không commit file này.

Task 3 dùng MarkItDown cho PDF/DOCX có text và Tesseract tiếng Việt cho PDF scan.
Cài OCR trên macOS: `brew install tesseract tesseract-lang`; trên Ubuntu:
`sudo apt-get install tesseract-ocr tesseract-ocr-vie`.
Nếu Tesseract đã có sẵn, có thể đặt `vie.traineddata` trong `.cache/tessdata/`.
Task 3 ưu tiên `2026_131_18_VBHN-VPQH.docx` có sẵn trong `data/landing/legal/`
thay cho PDF scan cùng Bộ luật; không cần URL tải cho file cục bộ.

Task 4 dùng `EMBEDDING_PROVIDER=openrouter`, `EMBEDDING_MODEL=baai/bge-m3`
và `OPENROUTER_API_KEY`; không cần tải model. Chroma lưu tại `chroma_db/` (không commit).
Để chạy local, dùng `EMBEDDING_PROVIDER=sentence_transformers`, `EMBEDDING_MODEL=BAAI/bge-m3`.

Task 6 dùng BM25 với term-frequency saturation và IDF dương; Task 7 gộp dense/BM25
bằng RRF. Task 9 chỉ dùng cosine score gốc để quyết định fallback.
`SCORE_THRESHOLD=0.5978` được thử trên 4 câu hỏi đúng chủ đề và 4 câu ngoài chủ đề;
đây là ngưỡng thử nghiệm ban đầu, cần đánh giá lại với golden dataset.

Task 10 dùng `LLM_PROVIDER=openrouter`, `LLM_MODEL=google/gemini-2.5-flash` và
`OPENROUTER_API_KEY`. Citation `[1]` tương ứng `sources[0]`, kể cả khi context được
đổi thứ tự. Thiếu bằng chứng, citation không hợp lệ hoặc provider lỗi sẽ trả lời từ chối xác minh.

Task 8 là fallback tùy chọn: điền `PAGEINDEX_API_KEY`, chạy
`python -m src.task8_pageindex_vectorless` để upload các PDF tạo từ Markdown chuẩn hóa,
rồi chờ PageIndex xử lý xong. ID tài liệu được cache trong `pageindex_doc_ids.json`;
nội dung thay đổi sẽ được upload lại. Tìm kiếm dùng PageIndex tree và LLM chọn section,
trả nguyên văn nội dung section. Không có key hoặc tài liệu chưa sẵn sàng thì giữ kết quả hybrid.
Nếu không tìm được font tiếng Việt, đặt `PAGEINDEX_FONT_PATH` tới file TTF phù hợp.

Chạy thử toàn bộ retrieval và generation: `python -m src.task10_generation`.

```bash
# 1. Thu thập và chuẩn hoá
python -m src.task1_collect_legal_docs
python -m src.task2_crawl_news
python -m src.task3_convert_markdown

# 2. Index và kiểm tra contract
python -m src.task4_chunking_indexing
pytest -q

# 3. Chạy sản phẩm
streamlit run app.py
```

## Lộ trình 3 giờ

| Mốc                  | Thời gian | Kết quả cần có                           |
| -------------------- | --------: | ---------------------------------------- |
| 0. Setup             |   10 phút | Môi trường và `.env` sẵn sàng            |
| 1. Data              |   25 phút | ≥3 legal, ≥5 news, Markdown đã chuẩn hoá |
| 2. Index & search    |   30 phút | ChromaDB, dense search và BM25 chạy được |
| 3. Fusion & fallback |   25 phút | RRF và fallback tuân thủ contract        |
| 4. Generation & UI   |   30 phút | Chatbot trả lời có citation              |
| 5. Evaluation        |   30 phút | 15+ Q&A, 4 metric, A/B comparison        |
| 6. Demo & handoff    |   30 phút | Test, report, demo và push repository    |

## Lưu ý quy tắc để có code quality tốt:

- Dense và BM25 nên cùng trả về `SearchResult` theo một schema.
- RRF chỉ nên dùng để gộp thứ hạng và chỉ chạy một lần.
- Fallback dùng cosine score gốc của dense retrieval.
- Threshold phải được hiệu chỉnh trên query in domain và out of domain, không có một con số đúng cho mọi corpus.

## Tài liệu

- [Module contracts](docs/MODULE_CONTRACTS.md): schema, interface và invariant mà code/test nên tuân theo.
- [Step-by-step guide](docs/STEP_BY_STEP.md): thứ tự triển khai và tiêu chí hoàn thành từng bước.
- [Grading rubric](docs/GRADING_RUBRIC.md): Rubric thang điểm.
- [Individual report](group_project/ịndividual/INDIVIDUAL_REPORT.md): template báo cáo cá nhân.
- [Suggested topics](docs/SUGGESTED_TOPICS.md): danh sách chủ đề tham khảo, không bắt buộc.

## Kiểm tra

```bash
# Contract tests
pytest tests/test_contracts.py -q

# Acceptance tests
pytest tests/test_acceptance.py -q

# Toàn bộ
pytest -q
```
