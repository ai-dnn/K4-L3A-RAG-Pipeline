"""
Task 3 â€” Chuáº©n hÃ³a dá»¯ liá»‡u sang Markdown.

HÆ°á»›ng dáº«n:
    1. DÃ¹ng MarkItDown Ä‘á»ƒ convert PDF/DOCX.
    2. Äá»c JSON vÃ  giá»¯ metadata á»Ÿ Ä‘áº§u file Markdown.
    3. Giá»¯ cáº¥u trÃºc thÆ° má»¥c legal/ vÃ  news/.
    4. KhÃ´ng táº¡o file rá»—ng hoáº·c file trÃ¹ng khi cháº¡y láº¡i.

CÃ i Ä‘áº·t:
    Dependency MarkItDown Ä‘Ã£ Ä‘Æ°á»£c khai bÃ¡o trong pyproject.toml.
    PDF scan cáº§n Tesseract vÃ  ngÃ´n ngá»¯ vie (macOS: brew install tesseract tesseract-lang).
    CÃ³ thá»ƒ Ä‘áº·t vie.traineddata trong .cache/tessdata/ cá»§a repo.
    
-> Hoáº·c dÃ¹ng cÃ´ng cá»¥ nÃ o báº¡n quen khÃ¡c Markitdown
"""

import json
from pathlib import Path

import fitz  # PyMuPDF
from markitdown import MarkItDown


LANDING_DIR = Path(__file__).parent.parent / "data" / "landing"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "standardized"

# Hai báº£n cá»§a cÃ¹ng Bá»™ luáº­t: Æ°u tiÃªn DOCX Ä‘á»ƒ trÃ¡nh lá»—i OCR vÃ  dá»¯ liá»‡u trÃ¹ng.
LEGAL_ALIASES = {
    "2026_131_18_VBHN-VPQH.docx": "bo_luat_lao_dong_18_vbhn_vpqh_2026",
}


def extract_pdf_text(path: Path) -> str:
    """Trích xuất text từ PDF bằng PyMuPDF (không cần Tesseract)."""
    pages = []
    with fitz.open(path) as doc:
        for index, page in enumerate(doc):
            text = page.get_text().strip()
            pages.append(text)
            print(f"Extract: {path.name} {index + 1}/{len(doc)}", flush=True)
    return "\n\n".join(pages).strip()


def convert_legal_docs() -> None:
    """Chuyá»ƒn PDF/DOCX sang Markdown."""
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
            content = extract_pdf_text(path)
        if not content:
            raise ValueError(f"No text extracted from {path.name}")
        header = f"# {stem.replace('_', ' ')}\n\n**Source:** {path.name}\n\n---\n\n"
        (output_dir / f"{stem}.md").write_text(header + content + "\n", encoding="utf-8")


def convert_news_articles() -> None:
    """Chuyá»ƒn JSON sang Markdown, giá»¯ tiÃªu Ä‘á» vÃ  metadata nguá»“n."""
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
    """Convert toÃ n bá»™ dá»¯ liá»‡u landing."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    convert_legal_docs()
    convert_news_articles()
    print(f"Saved Markdown to: {OUTPUT_DIR}")


if __name__ == "__main__":
    convert_all()
