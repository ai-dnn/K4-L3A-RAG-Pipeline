# Individual contribution report

## Thông tin

- Họ và tên: Đặng Quốc Hiệp
- Mã học viên: 2A202602755
- Nhóm: Nhóm RAG Pháp Luật Lao Động (K4-L3A)
- Repository/branch: `K4-L3A-RAG-Pipeline` / `dev`

## Phần việc đã thực hiện

| Module/deliverable | Việc tôi trực tiếp làm | File/commit/PR | Trạng thái |
|---|---|---|---|
| Streamlit Chatbot UI | Xây dựng giao diện chat hoàn chỉnh, kết nối pipeline RAG, hiển thị citation đa tầng, điểm tương đồng (score) và expander nguồn tham chiếu chi tiết | `app.py`, commit `a2f8a96` | Done |
| Golden Dataset | Xây dựng bộ dữ liệu kiểm thử chuẩn 16 câu hỏi - đáp pháp luật lao động (bao quát các trường hợp tra cứu số liệu, điều kiện loại trừ, quyền lợi NLĐ), gắn kèm expected context và ground truth | `group_project/evaluation/golden_dataset.json`, commit `8edc235` | Done |
| Đánh giá A/B & Báo cáo Benchmark | Thực hiện benchmark so sánh toàn diện Config A (Dense-only) và Config B (Hybrid + RRF) dựa trên 4 metric Ragas; phân tích định tính các case thất bại (worst performers) và đề xuất cải tiến | `group_project/evaluation/RESULT.md`, `reports/RESULT.md`, commit `8edc235` | Done |
| Kiến trúc & Biểu đồ trực quan | Thiết kế sơ đồ kiến trúc 6 giai đoạn của hệ thống RAG Hybrid và biểu đồ trực quan hóa so sánh tỷ lệ % hiệu năng A/B giữa 2 cấu hình | `docs/architecture_diagram.png` (commit `7349f9b`), `docs/metrics_comparison.png` (commit `ccc6811`) | Done |
| Tối ưu ChromaDB & Caching | Khắc phục lỗi đa kết nối ChromaDB bằng cách cache `PersistentClient` ở cấp module, tối ưu cơ chế nạp và giải phóng bộ nhớ, đảm bảo ghi index ổn định | `src/task4_chunking_indexing.py`, commit `43ac779` | Done |
| Cross-platform Testing | Sửa lỗi mã hóa ký tự `UnicodeDecodeError: 'charmap'` trên môi trường Windows bằng việc ép chuẩn `encoding='utf-8'` khi đọc/ghi file Markdown và tài liệu pháp lý | `tests/test_task4_indexing.py`, commit `8edc235` | Done |

## Quyết định kỹ thuật quan trọng

1. **Quyết định:** Thiết kế hệ thống Citation đa tầng (Inline Citation `[1]`, `[2]` liên kết trực tiếp với Metadata Expander chi tiết từng nguồn tài liệu, gồm doc_type, title, filename, cosine score và retrieval_method).  
   **Lý do/evidence:** Trong lĩnh vực tra cứu văn bản pháp luật, tính minh bạch và khả năng kiểm chứng nguồn (verifiability) là yêu cầu tiên quyết. Người dùng cần biết chính xác câu trả lời được trích từ Điều nào của Bộ luật Lao động hay Nghị định cụ thể nào, và phương thức truy hồi là ngữ nghĩa hay từ khóa.  
   **Trade-off:** Cần quản lý cấu trúc session state chi tiết hơn trong Streamlit để lưu vết cấu trúc `sources` song song với nội dung phản hồi, tránh thất lạc metadata qua các lượt hỏi đáp.

2. **Quyết định:** Xây dựng tập Golden Dataset 16 câu hỏi bao phủ cả trường hợp từ khóa số liệu cụ thể (tuổi nghỉ hưu, ngày nghỉ phép) và trường hợp điều kiện suy luận phức tạp (đơn phương chấm dứt HĐLĐ không cần báo trước).  
   **Lý do/evidence:** Kiểm thử và chứng minh rõ rệt thế mạnh của Hybrid Retrieval (kết hợp Dense Semantic Search và Lexical BM25 qua RRF) so với Dense-only. Kết quả đánh giá thực tế cho thấy Context Precision tăng từ 0.75 lên 0.89 (+14%) và Context Recall tăng từ 0.78 lên 0.91 (+13%).  
   **Trade-off:** Tốn thời gian thẩm định đối chiếu thủ công từng câu hỏi và trích đoạn context chuẩn trực tiếp từ văn bản quy phạm pháp luật gốc.

## Kiểm thử và kết quả

- Test hoặc query tôi đã dùng: Toàn bộ suite kiểm thử gồm 58 unit tests (`pytest -q`), trong đó có 15 test contracts và 5 test acceptance; bộ 16 câu hỏi Golden Dataset dùng cho đánh giá A/B pipeline.
- Kết quả trước/sau nếu có: Toàn bộ 58/58 test cases đều PASS (trước đó test acceptance thiếu golden dataset và test indexing bị lỗi font trên Windows). Đánh giá A/B cho thấy Config B (Hybrid + RRF) đạt điểm trung bình 0.9175, vượt trội +12.0% so với Config A (Dense-only đạt 0.7975).
- Lỗi đã phát hiện và cách xử lý:
  1. Lỗi `UnicodeDecodeError: 'charmap'` khi đọc file Markdown trên Windows -> Đã xử lý triệt để bằng cách bổ sung tham số `encoding='utf-8'` vào hàm `read_text()`.
  2. Hiện tượng tạo nhiều phiên kết nối ChromaDB gây lock thư mục cục bộ -> Đã xử lý bằng cách cache đối tượng `PersistentClient` tại module level và gọi `client._system.stop()` khi pipeline hoàn tất.

## Điều còn hạn chế

- Một hạn chế cụ thể của phần tôi làm: Giao diện Streamlit hiện chưa tích hợp chức năng cho người dùng tải lên trực tiếp văn bản pháp luật mới để re-index on-the-fly từ giao diện web mà vẫn dựa trên dữ liệu crawl/chuẩn hóa sẵn.
- Nếu có thêm thời gian, thay đổi đầu tiên tôi sẽ thực hiện: Bổ sung bộ lọc tài liệu thông minh (metadata filter theo năm ban hành, cơ quan ban hành, loại văn bản Luật/Nghị định) ngay trên sidebar của Streamlit trước khi gửi câu truy vấn tới bộ hybrid retrieval.

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc của mình và có thể giải thích hoặc chạy lại trong buổi demo.

- Ngày: 20/09/2026
- Tên thành viên: Đặng Quốc Hiệp (2A202602755)
