"""
Task 1 — Thu thập tài liệu chính sách/quy định.

Hướng dẫn:
    1. Chọn chủ đề của nhóm.
    2. Tìm tối thiểu 3 tài liệu PDF/DOCX từ nguồn công khai.
    3. Lưu file gốc vào data/landing/legal/.
    4. Đặt tên không dấu và thể hiện đúng nội dung.

Chủ đề: Bộ luật Lao động Việt Nam và các nghị định liên quan.
Nếu website chặn crawler, hãy chọn nguồn công khai khác; không vượt WAF.
"""

from pathlib import Path

import requests


DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "legal"

# Bản gốc công khai trên Cổng thông tin điện tử Chính phủ.
# Các nghị định là bản ban hành, không phải bản hợp nhất các sửa đổi sau này.
SOURCES = {
    "bo_luat_lao_dong_18_vbhn_vpqh_2026.pdf":
        "https://datafiles.chinhphu.vn/cpp/files/vbpq/2026/02/18-vbhn-vpqh.pdf",
    "nghi_dinh_145_2020_nd_cp_huong_dan_bo_luat_lao_dong.pdf":
        "https://datafiles.chinhphu.vn/cpp/files/vbpq/2020/12/145.signed.pdf",
    "nghi_dinh_12_2022_nd_cp_xu_phat_lao_dong.pdf":
        "https://datafiles.chinhphu.vn/cpp/files/vbpq/2022/01/12-2022-nd.signed.pdf",
}


def setup_directory() -> None:
    """Tạo thư mục lưu tài liệu gốc."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Ready: {DATA_DIR}")


def download_documents() -> None:
    """Tải 3 PDF luật lao động từ nguồn công khai."""
    for filename, url in SOURCES.items():
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        (DATA_DIR / filename).write_bytes(response.content)
        print(f"Saved: {filename}")


if __name__ == "__main__":
    setup_directory()
    download_documents()
