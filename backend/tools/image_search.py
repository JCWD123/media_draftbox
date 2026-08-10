"""
图片搜索工具 - 参考 hermes-agent 工具系统
"""
from tools import Tool, ToolResult
import requests
import yaml
from pathlib import Path


class ImageSearchTool(Tool):
    """图片搜索工具"""

    name = "image_search"
    description = "搜索图片（支持 Pexels API）"
    parameters = {
        "query": {"type": "string", "description": "搜索关键词", "required": True},
        "count": {"type": "integer", "description": "返回数量", "default": 12},
    }

    def execute(self, query: str, count: int = 12, **kwargs) -> ToolResult:
        config_file = Path.home() / ".draftbox" / "config.yaml"
        if not config_file.exists():
            return ToolResult(success=False, error="未配置 Pexels API Key")

        with open(config_file, encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}

        pexels_key = config.get("search", {}).get("pexels_key", "")
        if not pexels_key:
            return ToolResult(success=False, error="未配置 Pexels API Key")

        try:
            url = f"https://api.pexels.com/v1/search?query={query}&per_page={count}"
            headers = {"Authorization": pexels_key}
            response = requests.get(url, headers=headers, timeout=10)
            data = response.json()
            images = [
                {
                    "id": img["id"],
                    "url": img["src"]["large"],
                    "thumb": img["src"]["medium"],
                    "alt": img.get("alt", ""),
                    "author": img["photographer"],
                }
                for img in data.get("photos", [])
            ]
            return ToolResult(success=True, data=images)
        except Exception as e:
            return ToolResult(success=False, error=str(e))
