"""
新闻服务 - 调用 VPS API + 备用 RSS 源
"""
import requests
import feedparser
from typing import List, Dict

NEWS_API_BASE = "https://draftbox.arbismart.cloud/api/v1"

# 备用 RSS 源（当 VPS 不可用时）
FALLBACK_RSS = {
    "TECH": ["https://hnrss.org/frontpage"],
    "FINANCE": ["https://hnrss.org/frontpage"],
    "SOCIAL": ["https://hnrss.org/frontpage"],
    "DEVELOPER": ["https://hnrss.org/frontpage"],
    "VIDEO": ["https://hnrss.org/frontpage"],
    "COMMUNITY": ["https://hnrss.org/frontpage"],
    "KNOWLEDGE": ["https://hnrss.org/frontpage"],
}


def get_categories():
    """获取新闻分类"""
    try:
        resp = requests.get(f"{NEWS_API_BASE}/news/categories", timeout=5)
        data = resp.json()
        if data.get("data"):
            return data
    except:
        pass

    # 备用分类
    return {"data": [
        {"category_code": "FINANCE", "category_name": "财经金融", "icon": "trending_up", "color": "#FF6B6B"},
        {"category_code": "TECH", "category_name": "科技数码", "icon": "devices", "color": "#4ECDC4"},
        {"category_code": "SOCIAL", "category_name": "社会热点", "icon": "public", "color": "#45B7D1"},
        {"category_code": "DEVELOPER", "category_name": "开发者", "icon": "code", "color": "#96CEB4"},
        {"category_code": "VIDEO", "category_name": "视频平台", "icon": "play_circle", "color": "#DDA0DD"},
        {"category_code": "COMMUNITY", "category_name": "社区论坛", "icon": "forum", "color": "#A8E6CF"},
        {"category_code": "KNOWLEDGE", "category_name": "知识问答", "icon": "school", "color": "#FFD93D"},
    ]}


def get_news_list(category: str, page: int, page_size: int):
    """获取新闻列表"""
    # 尝试 VPS API
    try:
        resp = requests.get(
            f"{NEWS_API_BASE}/news/raw/list",
            params={"page": page, "page_size": page_size, "category": category, "days": 7},
            timeout=10
        )
        data = resp.json()
        if data.get("news"):
            news = []
            for item in data.get("news", []):
                news.append({
                    "title": item.get("title", ""),
                    "summary": "",
                    "link": item.get("url", ""),
                    "published": item.get("news_date", "")[:10],
                    "source": item.get("source_name", ""),
                    "category": item.get("category", ""),
                })
            return {"news": news, "category": category, "total": data.get("total", 0)}
    except:
        pass

    # 备用 RSS 源
    try:
        rss_sources = FALLBACK_RSS.get(category, FALLBACK_RSS["TECH"])
        news = []
        for source in rss_sources:
            feed = feedparser.parse(source)
            for entry in feed.entries[:page_size]:
                news.append({
                    "title": entry.get("title", ""),
                    "summary": entry.get("summary", "")[:200],
                    "link": entry.get("link", ""),
                    "published": entry.get("published", "")[:10],
                    "source": feed.feed.get("title", "RSS"),
                    "category": category,
                })
        return {"news": news[:page_size], "category": category, "total": len(news)}
    except:
        pass

    return {"news": [], "category": category, "total": 0, "error": "VPS 和 RSS 源均不可用"}
