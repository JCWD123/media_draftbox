"""
新闻获取工具 - 参考 hermes-agent 工具系统
"""
from tools import Tool, ToolResult
import requests


class NewsFetchTool(Tool):
    """新闻获取工具"""

    name = "news_fetch"
    description = "获取热点新闻（从 VPS 同步）"
    parameters = {
        "category": {"type": "string", "description": "新闻分类", "default": "TECH"},
        "count": {"type": "integer", "description": "返回数量", "default": 20},
    }

    def execute(self, category: str = "TECH", count: int = 20, **kwargs) -> ToolResult:
        try:
            url = "https://draftbox.arbismart.cloud/api/v1/news/raw/list"
            params = {"page": 1, "page_size": count, "category": category, "days": 7}
            response = requests.get(url, params=params, timeout=15)
            data = response.json()
            news = [
                {
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "source": item.get("source_name", ""),
                    "date": item.get("news_date", "")[:10],
                }
                for item in data.get("news", [])
            ]
            return ToolResult(
                success=True,
                data={
                    "news": news,
                    "total": data.get("total", 0),
                    "category": category,
                }
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))
