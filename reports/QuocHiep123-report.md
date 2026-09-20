# Individual contribution report

## Thông tin

- Họ và tên: Đặng Quốc Hiệp
- Mã học viên: QuocHiep123
- Nhóm: Nhóm RAG Pháp Luật Lao Động
- Repository/branch: `K4-L3A-RAG-Pipeline` / `dev`

## Phần việc đã thực hiện

| Module/deliverable | Việc tôi trực tiếp làm | File/commit/PR | Trạng thái |
|---|---|---|---|
| Streamlit Chatbot UI | Xây dựng giao diện chat hoàn chỉnh, kết nối pipeline RAG, hiển thị citation metadata, điểm số score và expander nguồn tham chiếu | `app.py`, commit `a2f8a96` | Done |
| Golden Dataset | Xây dựng bộ 16 câu hỏi - đáp chuẩn đối soát (grounded cases) bao quát quy định lao động | `group_project/evaluation/golden_dataset.json` | Done |
| Đánh giá A/B & Báo cáo | Thực hiện hoàn thiện báo cáo phân tích hiệu năng A/B, 4 metric Ragas, phân tích điểm yếu (worst performers) và đề xuất | `group_project/evaluation/RESULT.md` | Done |
| Cross-platform Testing | Tối ưu hóa tương thích Windows cho file conversion tests (sửa mã hóa UTF-8 cho pathlib) | `tests/test_task4_indexing.py` | Done |

## Quyết định kỹ thuật quan trọng

1. **Quyết định:** Hiển thị trích dẫn phân cấp (expander) kèm thông tin phương thức truy hồi (`retrieval_method`) và điểm tương đồng trong Streamlit UI.  
   **Lý do/evidence:** Người dùng tra cứu văn bản pháp luật cần sự minh bạch tuyệt đối; việc thấy rõ câu trả lời lấy từ Điều nào, Nghị định nào và độ tin cậy bao nhiêu giúp tăng tính tin cậy pháp lý.  
   **Trade-off:** Giao diện cần xử lý session state chi tiết hơn để lưu trữ cấu trúc `sources` song song với chuỗi `answer`.

2. **Quyết định:** Xây dựng tập Golden Dataset 16 câu bao phủ cả trường hợp số liệu cụ thể (tuổi nghỉ hưu, ngày nghỉ) và trường hợp điều kiện loại trừ (đơn phương chấm dứt HĐLĐ không cần báo trước).  
   **Lý do/evidence:** Kiểm thử được khả năng phân biệt giữa dense search (dễ hiểu nhầm sang điều khoản chung) và lexical BM25 (chính xác theo từ khóa số liệu).  
   **Trade-off:** Tốn thời gian thẩm định đối chiếu thủ công từng câu hỏi với văn bản luật gốc.

## Kiểm thử và kết quả

- Test hoặc query tôi đã dùng: Toàn bộ suite kiểm thử gồm 58 unit tests (`pytest -q`), trong đó có 15 test contracts và 5 test acceptance.
- Kết quả trước/sau nếu có: Toàn bộ 58/58 test cases đều PASS (trước đó test acceptance thiếu dataset và test indexing bị lỗi font trên Windows).
- Lỗi đã phát hiện và cách xử lý: Lỗi `UnicodeDecodeError: 'charmap'` khi đọc file Markdown trên môi trường Windows; đã xử lý bằng cách bổ sung `encoding='utf-8'` vào `read_text()`.

## Điều còn hạn chế

- Một hạn chế cụ thể của phần tôi làm: Giao diện Streamlit hiện chưa tích hợp chức năng cho người dùng tải lên trực tiếp tài liệu mới để re-index tức thời từ giao diện web.
- Nếu có thêm thời gian, thay đổi đầu tiên tôi sẽ thực hiện: Bổ sung tính năng lọc tài liệu theo từng bộ luật/nghị định ngay trên thanh sidebar trước khi truy vấn.

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc của mình và có thể giải thích hoặc chạy lại trong buổi demo.

- Ngày: 20/09/2026
- Tên thành viên: Đặng Quốc Hiệp
