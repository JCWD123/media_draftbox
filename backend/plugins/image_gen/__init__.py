"""
图片生成插件 - 参考 hermes-agent 插件系统
"""
from plugins import Plugin
from typing import Any, Dict
import requests
import yaml
from pathlib import Path


class ImageGenPlugin(Plugin):
    """图片生成插件"""

    name = "image_gen"
    description = "AI 图片生成（支持多个 provider）"
    version = "1.0.0"

    def initialize(self) -> bool:
        """初始化插件"""
        config_file = Path.home() / ".draftbox" / "config.yaml"
        if config_file.exists():
            with open(config_file, encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}
            self.api_key = config.get("image_gen", {}).get("api_key", "")
            self.provider = config.get("image_gen", {}).get("provider", "pexels")
        return True

    def execute(self, prompt: str, **kwargs) -> Any:
        """生成图片"""
        if self.provider == "pexels":
            return self._search_pexels(prompt, **kwargs)
        return {"error": f"不支持的 provider: {self.provider}"}

    def _search_pexels(self, query: str, count: int = 1, **kwargs) -> dict:
        """使用 Pexels 搜索图片"""
        if not self.api_key:
            return {"error": "未配置 Pexels API Key"}

        try:
            url = f"https://api.pexels.com/v1/search?query={query}&per_page={count}"
            headers = {"Authorization": self.api_key}
            response = requests.get(url, headers=headers, timeout=10)
            data = response.json()
            images = [
                {
                    "url": img["src"]["large"],
                    "thumb": img["src"]["medium"],
                    "alt": img.get("alt", ""),
                    "author": img["photographer"],
                }
                for img in data.get("photos", [])
            ]
            return {"images": images, "source": "pexels"}
        except Exception as e:
            return {"error": str(e)}
