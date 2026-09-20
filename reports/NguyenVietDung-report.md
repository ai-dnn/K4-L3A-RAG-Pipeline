# Individual contribution report

## Thông tin

- Họ và tên: Nguyễn Việt Dũng
- Mã học viên: (Thành viên nhóm)
- Nhóm: Nhóm RAG Pháp Luật Lao Động (Đặng Quốc Hiệp - 2A202602755, Nguyễn Việt Dũng, Nguyễn Thế Khang)
- Repository/branch: `K4-L3A-RAG-Pipeline` / `main`

## Phần việc đã thực hiện

| Module/deliverable | Việc tôi trực tiếp làm | File/commit/PR | Trạng thái |
|---|---|---|---|
| Thu thập văn bản pháp luật & tin tức | Thu thập 3 bộ tài liệu pháp lý cốt lõi (Bộ luật Lao động 2019/2026, Nghị định 12/2022/NĐ-CP, Nghị định 145/2020/NĐ-CP) và crawl 5 bài viết chuyên sâu về quan hệ lao động | `src/task1_collect_legal_docs.py`, `src/task2_crawl_news.py`, `data/landing/` | Done |
| Chuẩn hóa Markdown & OCR Fallback | Xây dựng pipeline chuyển đổi file DOCX và PDF sang định dạng Markdown chuẩn hóa bằng MarkItDown; tích hợp cơ chế OCR tiếng Việt cho tài liệu scan | `src/task3_convert_markdown.py`, `data/standardized/` | Done |
| Phân đoạn văn bản (Chunking) | Thiết lập giải thuật RecursiveCharacterTextSplitter chia nhỏ tài liệu theo ranh giới đoạn/câu với chunk size = 500 ký tự và overlap = 100 ký tự, bảo toàn metadata điều luật | `src/task4_chunking_indexing.py` | Done |
| Vector Database Indexing | Xây dựng pipeline sinh embedding đa ngôn ngữ với mô hình `BAAI/bge-m3` và nạp toàn bộ vector vào cơ sở dữ liệu ChromaDB cục bộ | `src/task4_chunking_indexing.py`, `chroma_db/` | Done |
| Kiểm thử Data & Indexing | Xây dựng và thực thi các bài unit test kiểm tra tính toàn vẹn metadata, tính ổn định của chunk id và không trùng lặp dữ liệu | `tests/test_task4_indexing.py` | Done |

## Quyết định kỹ thuật quan trọng

1. **Quyết định:** Ưu tiên nạp trực tiếp file DOCX gốc `2026_131_18_VBHN-VPQH.docx` thay vì chạy OCR trên file PDF scan dung lượng lớn gần 40MB.  
   **Lý do/evidence:** Xử lý file DOCX bằng MarkItDown cho tốc độ nhanh hơn gấp 10 lần và độ chính xác văn bản đạt 100%, loại bỏ hoàn toàn các lỗi mất dấu hoặc biến dạng ký tự tiếng Việt thường gặp khi dùng OCR.  
   **Trade-off:** Cần xây dựng cơ chế ánh xạ `LEGAL_ALIASES` để hệ thống tự động phát hiện và đồng bộ hóa tên file đầu ra chuẩn `bo_luat_lao_dong_18_vbhn_vpqh_2026.md`.

2. **Quyết định:** Thiết lập kích thước Chunk size = 500 ký tự và Overlap = 100 ký tự trên các điểm ngắt đoạn logic (`\n\n`, `\n`, `. `, ` `).  
   **Lý do/evidence:** Kích thước này tương ứng vừa vặn với độ dài trung bình của một khoản hoặc một điểm trong điều luật lao động, tránh việc một điều khoản bị chia cắt rời rạc sang 2 chunk khác nhau làm mất ngữ cảnh khi truy hồi.  
   **Trade-off:** Số lượng chunk tăng lên khoảng 30% so với chunk 1000 ký tự, làm tăng nhẹ thời gian tạo embedding ban đầu nhưng bù lại tăng độ liên quan (Context Precision).

## Kiểm thử và kết quả

- Test hoặc query tôi đã dùng: Unit test `tests/test_task4_indexing.py` kiểm tra nạp tài liệu, tách chunk và chuẩn hóa embedding vector.
- Kết quả trước/sau nếu có: Đã chuẩn hóa thành công 3 văn bản pháp luật lớn và 5 bài báo tin tức thành 100% tài liệu Markdown cấu trúc chuẩn, trích xuất đầy đủ metadata (title, source, doc_type, url) mà không xảy ra hiện tượng rỗng dữ liệu.
- Lỗi đã phát hiện và cách xử lý: Lỗi văn bản DOCX chứa các khoảng trắng thừa và ngắt dòng liên tiếp gây gián đoạn câu -> Bổ sung hàm regex làm sạch whitespace và chuẩn hóa tiêu đề trước khi đưa vào text splitter.

## Điều còn hạn chế

- Một hạn chế cụ thể của phần tôi làm: Hiện tại văn bản vẫn được phân đoạn dựa trên ngưỡng ký tự thay vì bóc tách chuyên sâu theo cây phân cấp Chương - Mục - Điều của văn bản quy phạm pháp luật.
- Nếu có thêm thời gian, thay đổi đầu tiên tôi sẽ thực hiện: Xây dựng một Legal Semantic Chunker chuyên biệt tự động nhận diện cú pháp "Điều X. Tên điều" và "Khoản Y" để phân chia chunk chính xác theo từng đơn vị pháp lý độc lập.

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc của mình và có thể giải thích hoặc chạy lại trong buổi demo.

- Ngày: 20/09/2026
- Tên thành viên: Nguyễn Việt Dũng
