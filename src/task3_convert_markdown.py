"""
Task 3 — Chuẩn hóa dữ liệu sang Markdown.

Hướng dẫn:
    1. Dùng MarkItDown để convert PDF/DOCX.
    2. Đọc JSON và giữ metadata ở đầu file Markdown.
    3. Giữ cấu trúc thư mục legal/ và news/.
    4. Không tạo file rỗng hoặc file trùng khi chạy lại.

Cài đặt:
    Dependency MarkItDown đã được khai báo trong pyproject.toml.
    PDF scan cần Tesseract và ngôn ngữ vie (macOS: brew install tesseract tesseract-lang).
    Có thể đặt vie.traineddata trong .cache/tessdata/ của repo.
    
-> Hoặc dùng công cụ nào bạn quen khác Markitdown
"""

import json
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

import pypdfium2 as pdfium
from markitdown import MarkItDown


LANDING_DIR = Path(__file__).parent.parent / "data" / "landing"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "standardized"

# Hai bản của cùng Bộ luật: ưu tiên DOCX để tránh lỗi OCR và dữ liệu trùng.
LEGAL_ALIASES = {
    "2026_131_18_VBHN-VPQH.docx": "bo_luat_lao_dong_18_vbhn_vpqh_2026",
}


def ocr_pdf(path: Path) -> str:
    """Đọc PDF scan bằng Tesseract tiếng Việt, từng trang để hạn chế RAM."""
    command = ["tesseract", "stdin", "stdout", "-l", "vie"]
    tessdata = Path(__file__).parent.parent / ".cache" / "tessdata"
    if (tessdata / "vie.traineddata").is_file():
        command.extend(["--tessdata-dir", str(tessdata)])
    pages = []
    with pdfium.PdfDocument(path) as pdf, TemporaryDirectory() as temporary_dir:
        image_path = Path(temporary_dir) / "page.png"
        for index in range(len(pdf)):
            page = pdf[index]
            try:
                bitmap = page.render(scale=3)
                try:
                    bitmap.to_pil().save(image_path)
                finally:
                    bitmap.close()
            finally:
                page.close()
            result = subprocess.run(
                command, input=image_path.read_bytes(), capture_output=True, check=True,
            )
            pages.append(result.stdout.decode("utf-8").strip())
            print(f"OCR: {path.name} {index + 1}/{len(pdf)}", flush=True)
    return "\n\n".join(pages).strip()


def convert_legal_docs() -> None:
    """Chuyển PDF/DOCX sang Markdown."""
    output_dir = OUTPUT_DIR / "legal"
    output_dir.mkdir(parents=True, exist_ok=True)
    converter = MarkItDown()
    sources = {}
    for path in sorted((LANDING_DIR / "legal").iterdir()):
        if path.is_file() and path.suffix.lower() in {".pdf", ".docx"}:
            stem = LEGAL_ALIASES.get(path.name, path.stem)
            if stem not in sources or path.suffix.lower() == ".docx":
                sources[stem] = path
    for stem, path in sources.items():
        content = converter.convert(str(path)).text_content.strip()
        if not content and path.suffix.lower() == ".pdf":
            content = ocr_pdf(path)
        if not content:
            raise ValueError(f"No text extracted from {path.name}")
        header = f"# {stem.replace('_', ' ')}\n\n**Source:** {path.name}\n\n---\n\n"
        (output_dir / f"{stem}.md").write_text(header + content + "\n", encoding="utf-8")


def convert_news_articles() -> None:
    """Chuyển JSON sang Markdown, giữ tiêu đề và metadata nguồn."""
    output_dir = OUTPUT_DIR / "news"
    output_dir.mkdir(parents=True, exist_ok=True)
    for path in sorted((LANDING_DIR / "news").glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        content = data["content_markdown"].strip()
        if not content:
            raise ValueError(f"Empty article: {path.name}")
        header = (
            f"# {data['title']}\n\n"
            f"**Source:** {data['url']}\n\n"
            f"**Crawled:** {data['date_crawled']}\n\n---\n\n"
        )
        (output_dir / f"{path.stem}.md").write_text(header + content + "\n", encoding="utf-8")


def convert_all() -> None:
    """Convert toàn bộ dữ liệu landing."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    convert_legal_docs()
    convert_news_articles()
    print(f"Saved Markdown to: {OUTPUT_DIR}")


if __name__ == "__main__":
    convert_all()
