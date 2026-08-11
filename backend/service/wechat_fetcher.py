"""
公众号文章抓取 - HTTP 多策略（微信反爬时返回 None，由爬虫代理/手动粘贴降级）
- 图片真实 URL 在 data-src 属性（Go 版 Bug 53 教训）
"""
import re
from typing import Dict, List, Optional

import requests
from bs4 import BeautifulSoup

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


def fetch_url(url: str, timeout: int = 20) -> Optional[Dict]:
    """抓取公众号文章，返回 {"title", "content", "images"}；失败返回 None"""
    try:
        resp = requests.get(url, headers={"User-Agent": UA}, timeout=timeout)
        if resp.status_code != 200:
            return None
        html = resp.text
    except Exception:
        return None

    # 微信验证码/环境异常页
    if "环境异常" in html or "verify" in url or "mp.weixin.qq.com/s?" not in url and len(html) < 2000:
        pass

    soup = BeautifulSoup(html, "html.parser")
    title = ""
    title_tag = soup.find("h1", class_="rich_media_title") or soup.find("h1")
    if title_tag:
        title = title_tag.get_text(strip=True)

    content = ""
    js_content = soup.find("div", id="js_content")
    if js_content:
        content = js_content.get_text("\n", strip=True)

    # 图片：data-src 优先（微信真实图床地址），其次 src
    images: List[str] = []
    for img in (js_content or soup).find_all("img"):
        src = img.get("data-src") or img.get("src") or ""
        if src.startswith("http") and src not in images:
            images.append(src)
        if len(images) >= 10:
            break

    if not content:
        return None
    return {"title": title or url, "content": content[:50000], "images": images}
