"""
Task 2 — Crawl bài viết/thông báo.

Hướng dẫn:
    1. Điền tối thiểu 5 URL công khai vào ARTICLE_URLS.
    2. Crawl từng URL bằng Crawl4AI.
    3. Lưu mỗi bài thành một JSON trong data/landing/news/.
    4. Giữ đủ url, title, date_crawled và content_markdown.

Cài browser trước khi chạy:
    python -m playwright install chromium
    
-> Dùng Firecrawl or bất cứ công cụ nào bạn quen    
"""

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

from crawl4ai import AsyncWebCrawler


DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "news"

ARTICLE_URLS = [
    "https://baochinhphu.vn/17-diem-moi-noi-bat-cua-bo-luat-lao-dong-2019-102267514.htm",
    "https://baochinhphu.vn/nhieu-diem-moi-trong-bo-luat-lao-dong-ve-hop-dong-lao-dong-102267368.htm",
    "https://baochinhphu.vn/quy-dinh-ve-thoi-gio-nghi-ngoi-theo-bo-luat-lao-dong-moi-102294141.htm",
    "https://baochinhphu.vn/ky-hop-dong-thu-viec-co-phai-dong-bhxh-khong-102287850.htm",
    "https://baochinhphu.vn/truong-hop-nao-bi-coi-la-cham-dut-hop-dong-lao-dong-trai-luat-102220905124022519.htm",
]


async def crawl_article(url: str) -> dict:
    """Crawl một bài viết và giữ metadata cho bước chuẩn hóa."""
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url)
        if not result.success or not result.markdown:
            raise RuntimeError(result.error_message or f"No content: {url}")
        return {
            "url": url,
            "title": (result.metadata or {}).get("title") or url,
            "date_crawled": datetime.now(timezone.utc).isoformat(),
            "content_markdown": result.markdown.raw_markdown,
        }


async def crawl_all() -> None:
    """Crawl và lưu từng bài thành một file JSON."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    for index, url in enumerate(ARTICLE_URLS, 1):
        try:
            article = await crawl_article(url)
            output = DATA_DIR / f"article_{index:02d}.json"
            output.write_text(
                json.dumps(article, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            print(f"Saved: {output}")
        except Exception as error:
            print(f"Failed: {url} — {error}")


if __name__ == "__main__":
    asyncio.run(crawl_all())
