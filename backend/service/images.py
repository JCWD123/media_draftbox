"""
图片搜索服务 - Pexels API
"""
import requests
import yaml
from pathlib import Path

CONFIG_FILE = Path.home() / ".draftbox" / "config.yaml"


def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


def search_images(query: str, count: int):
    """搜索图片"""
    config = load_config()
    pexels_key = config.get("search", {}).get("pexels_key", "")

    if pexels_key:
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
                    "source": "pexels"
                }
                for img in data.get("photos", [])
            ]
            return {"images": images, "source": "pexels"}
        except:
            pass

    return {"images": [], "error": "未配置图片搜索 API"}
