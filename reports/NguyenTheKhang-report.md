# Individual contribution report

## Thông tin

- Họ và tên: Nguyễn Thế Khang
- Mã học viên: (Thành viên nhóm)
- Nhóm: Nhóm RAG Pháp Luật Lao Động (Đặng Quốc Hiệp - 2A202602755, Nguyễn Việt Dũng, Nguyễn Thế Khang)
- Repository/branch: `K4-L3A-RAG-Pipeline` / `main`

## Phần việc đã thực hiện

| Module/deliverable | Việc tôi trực tiếp làm | File/commit/PR | Trạng thái |
|---|---|---|---|
| Dense Semantic Search | Triển khai hàm truy hồi ngữ nghĩa từ cơ sở dữ liệu ChromaDB, tính toán độ tương đồng Cosine score và sắp xếp top chunks | `src/task5_semantic_search.py` | Done |
| Lexical BM25 Search | Xây dựng bộ tìm kiếm từ khóa chính xác BM25Plus, xử lý token hóa tiếng Việt và kiểm soát hiện tượng bão hòa tần suất từ khóa | `src/task6_lexical_search.py` | Done |
| RRF Reranking & Retrieval Pipeline | Cài đặt thuật toán Reciprocal Rank Fusion (hằng số $k=60$) kết hợp thứ hạng Dense + BM25; thiết lập cơ chế kiểm tra ngưỡng cosine score (threshold = 0.5978) cho Fallback | `src/task7_reranking.py`, `src/task9_retrieval_pipeline.py` | Done |
| Vectorless PageIndex Fallback | Xây dựng nhánh dự phòng vectorless sử dụng PageIndex duyệt cấu trúc cây mục lục văn bản khi điểm số tương đồng dưới ngưỡng quy định | `src/task8_pageindex_vectorless.py` | Done |
| Generation có Citation & Safe Refusal | Thiết kế prompt LLM sinh câu trả lời kèm citation `[1]`, `[2]` trích dẫn chính xác từ `sources`, tích hợp cơ chế safe refusal khi thiếu căn cứ pháp lý | `src/task10_generation.py`, `src/retrieval_context.py`, `src/llm.py` | Done |
| Kiểm thử Pipeline Contracts | Thực hiện kiểm thử tuân thủ hợp đồng giao tiếp dữ liệu giữa các module retrieval, reranking và generation | `tests/test_tasks7_to10.py`, `tests/test_task5_semantic_search.py`, `tests/test_task6_lexical_search.py` | Done |

## Quyết định kỹ thuật quan trọng

1. **Quyết định:** Sử dụng giải thuật BM25Plus thay vì BM25Okapi truyền thống trong thành phần tìm kiếm từ khóa.  
   **Lý do/evidence:** BM25Plus có tham số bù $\delta = 1.0$ giải quyết triệt để vấn đề IDF bị âm hoặc bằng 0 khi thuật ngữ pháp lý xuất hiện nhiều lần trong corpus nhỏ, giúp nâng cao Context Recall cho các câu hỏi tra cứu theo số hiệu điều luật hoặc từ viết tắt.  
   **Trade-off:** Cần thêm bước tính toán trọng số điều chỉnh trong vòng lặp tính điểm token, tuy nhiên chi phí tính toán là không đáng kể (chạy in-memory trong vài mili-giây).

2. **Quyết định:** Áp dụng cơ chế Fallback sang câu từ chối an toàn (Safe Refusal) khi điểm tương đồng dense cosine gốc < 0.5978 hoặc context không chứa đủ bằng chứng.  
   **Lý do/evidence:** Trong nghiệp vụ tư vấn pháp luật, việc ngăn chặn hoàn toàn hiện tượng ảo giác (hallucination) quan trọng hơn việc cố gắng trả lời một câu hỏi không chắc chắn. Ngưỡng 0.5978 đã được hiệu chuẩn thực nghiệm trên các câu hỏi in-domain và out-of-domain.  
   **Trade-off:** Một số câu hỏi diễn đạt quá trừu tượng hoặc dùng từ ngữ địa phương có thể bị hệ thống từ chối trả lời nếu không khớp ngữ nghĩa với tài liệu luật hiện có.

## Kiểm thử và kết quả

- Test hoặc query tôi đã dùng: Bộ test contracts `tests/test_tasks7_to10.py`, test semantic search `tests/test_task5_semantic_search.py`, test lexical search `tests/test_task6_lexical_search.py`, và test mở rộng ngữ cảnh `tests/test_retrieval_context.py`.
- Kết quả trước/sau nếu có: Tất cả các contract tests đều PASS; RRF đảm bảo không có chunk bị nhân đôi ID và điểm số thứ hạng giảm dần đều; hàm sinh câu trả lời luôn bảo đảm gán đúng chỉ số citation khớp với thứ tự trong `sources`.
- Lỗi đã phát hiện và cách xử lý: Khi tái sắp xếp context (reordering), thứ tự hiển thị của các chunk bị đảo lộn dẫn đến chỉ số `[1]`, `[2]` trong văn bản không khớp với danh sách nguồn ban đầu -> Đã khắc phục bằng cách lưu vết `sources` với index cố định và truyền mapping tường minh vào prompt template.

## Điều còn hạn chế

- Một hạn chế cụ thể của phần tôi làm: Nhánh PageIndex fallback hiện vẫn phụ thuộc vào kết nối API bên ngoài nên có độ trễ lớn hơn so với nhánh Hybrid retrieval cục bộ.
- Nếu có thêm thời gian, thay đổi đầu tiên tôi sẽ thực hiện: Triển khai một Cross-Encoder Reranker cục bộ (ví dụ: `BAAI/bge-reranker-v2-m3`) để so sánh hiệu quả xếp hạng trực tiếp với thuật toán RRF.

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc của mình và có thể giải thích hoặc chạy lại trong buổi demo.

- Ngày: 20/09/2026
- Tên thành viên: Nguyễn Thế Khang
