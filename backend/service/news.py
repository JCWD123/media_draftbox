"""
新闻服务 - 调用 VPS API
"""
import requests

NEWS_API_BASE = "https://draftbox.arbismart.cloud/api/v1"


def get_categories():
    """获取新闻分类"""
    try:
        resp = requests.get(f"{NEWS_API_BASE}/news/categories", timeout=10)
        return resp.json()
    except:
        return {"data": [
            {"category_code": "FINANCE", "category_name": "财经金融", "icon": "trending_up"},
            {"category_code": "TECH", "category_name": "科技数码", "icon": "devices"},
            {"category_code": "SOCIAL", "category_name": "社会热点", "icon": "public"},
            {"category_code": "DEVELOPER", "category_name": "开发者", "icon": "code"},
            {"category_code": "VIDEO", "category_name": "视频平台", "icon": "play_circle"},
            {"category_code": "COMMUNITY", "category_name": "社区论坛", "icon": "forum"},
            {"category_code": "KNOWLEDGE", "category_name": "知识问答", "icon": "school"},
        ]}


def get_news_list(category: str, page: int, page_size: int):
    """获取新闻列表"""
    try:
        resp = requests.get(
            f"{NEWS_API_BASE}/news/raw/list",
            params={"page": page, "page_size": page_size, "category": category, "days": 7},
            timeout=15
        )
        data = resp.json()
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
    except Exception as e:
        return {"news": [], "error": str(e)}
