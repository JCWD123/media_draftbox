"""
自定义新闻搜索源 - 基于 ddgs (DuckDuckGo) 实时搜索
用于在 draftbox 中搜索 AI 圈子/技术类实时新闻，结果可勾选并作为写作素材
"""
import hashlib
import re
import threading
from typing import List, Dict

try:
    from ddgs import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    DDGS_AVAILABLE = False

# 搜索结果缓存：id → item（供 fetch_news_by_ids 回查，勾选后 AI 写作能拿到）
SEARCH_CACHE: Dict[str, Dict] = {}
_CACHE_LOCK = threading.Lock()
_CACHE_MAX = 200


def _item_id(url: str) -> str:
    if not url:
        import random
        return f"s{random.randint(100000, 999999)}"
    return hashlib.md5(url.encode("utf-8")).hexdigest()[:8]


def search_news(query: str, limit: int = 12, region: str = "cn-zh", language: str = "zh-cn") -> dict:
    """按关键词搜索新闻（DuckDuckGo 实时搜索结果）

    优先用 news()，失败降级 text()。返回 draftbox 标准新闻结构，
    并把结果写入 SEARCH_CACHE 供回查。
    """
    if not DDGS_AVAILABLE:
        return {"news": [], "total": 0, "error": "ddgs 未安装，请先 pip install ddgs"}
    if not query or not query.strip():
        return {"news": [], "total": 0, "error": "请提供搜索关键词"}

    query = query.strip()
    results = None
    err_detail = ""

    # 尝试 news() 与 text() 两种后端，任一成功即可
    try:
        with DDGS() as d:
            results = list(d.news(query, region=region, safesearch="moderate", max_results=limit))
    except Exception as e:
        err_detail = str(e)[:80]
        results = None

    source_backend = "news"

    if not results:
        # 降级：普通网页搜索（更稳定）
        try:
            with DDGS() as d:
                text_results = list(d.text(query, region=region, max_results=limit))
            if text_results:
                results = []
                for item in text_results:
                    results.append({
                        "title": item.get("title", ""),
                        "body": item.get("body") or "",
                        "url": item.get("href", ""),
                        "date": "",
                    })
                source_backend = "text"
        except Exception as e:
            err_detail += (" | " if err_detail else "") + str(e)[:80]

    if not results:
        return {"news": [], "total": 0, "error": f"搜索失败: {err_detail or 'No results found.'}"}

    news = []
    seen = set()
    for item in results:
        url = item.get("url") or ""
        title = item.get("title") or ""
        if not url or not title or url in seen:
            continue
        seen.add(url)
        nid = _item_id(url)
        # 来源：优先 item.source，否则从 URL 提取域名
        if item.get("source"):
            source = item.get("source")
        else:
            m = re.search(r"https?://([^/]+)", url)
            source = m.group(1) if m else "DDG"
        entry = {
            "id": nid,
            "title": title,
            "summary": (item.get("body") or item.get("description") or "")[:300],
            "link": url,
            "published": (item.get("date") or "")[:10],
            "source": source,
            "category": "SEARCH",
            "_backend": source_backend,
            "_cn": _cn_ratio(title, item.get("body") or ""),
        }
        with _CACHE_LOCK:
            SEARCH_CACHE[nid] = entry
            while len(SEARCH_CACHE) > _CACHE_MAX:
                SEARCH_CACHE.pop(next(iter(SEARCH_CACHE)))
        news.append(entry)
        if len(news) >= limit:
            break

    # 中文优先排序（标题/正文中文字符占比高的靠前），保持用户对中文新闻的期望
    news.sort(key=lambda x: x.get("_cn", 0), reverse=True)
    return {"news": news, "total": len(news), "query": query}


def _cn_ratio(title: str, body: str) -> float:
    """估算一条结果的中文含量（标题+正文中文字符占比），用于中文优先排序"""
    text = (title + " " + body)
    if not text.strip():
        return 0.0
    cn = len(re.findall(r"[\u4e00-\u9fff]", text))
    return cn / max(len(text), 1) * 100  # 千分位


def get_from_cache(ids: List[str]) -> List[Dict]:
    """按 id 从搜索缓存回查（勾选后 AI 写作用）"""
    with _CACHE_LOCK:
        return [SEARCH_CACHE[i] for i in ids if i in SEARCH_CACHE]
