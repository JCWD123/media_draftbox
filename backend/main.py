"""
DraftBox 后端 - FastAPI + wewrite + LanguageTool + Unsplash + 热点新闻（调用VPS API）
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import subprocess
import os
import json
import yaml
import requests
from pathlib import Path

app = FastAPI(title="DraftBox API")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

CONFIG_FILE = Path.home() / ".draftbox" / "config.yaml"

def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}

DRAFTS_DIR = Path.home() / ".draftbox" / "drafts"
DRAFTS_DIR.mkdir(parents=True, exist_ok=True)

# VPS 新闻 API 地址
NEWS_API_BASE = "https://draftbox.arbismart.cloud/api/v1"

class ConvertRequest(BaseModel):
    markdown: str
    theme: str = "professional-clean"

class DraftSaveRequest(BaseModel):
    title: str
    content: str

class GrammarCheckRequest(BaseModel):
    text: str
    language: str = "zh"

class ImageSearchRequest(BaseModel):
    query: str
    count: int = 12

class NewsRequest(BaseModel):
    category: str = "TECH"
    page: int = 1
    page_size: int = 20


# ========== 热点新闻 API（调用VPS） ==========

@app.get("/api/news/categories")
async def news_categories():
    """获取新闻分类（从VPS同步）"""
    try:
        resp = requests.get(f"{NEWS_API_BASE}/news/categories", timeout=10)
        return resp.json()
    except:
        # 本地备用分类
        return {"data": [
            {"category_code": "FINANCE", "category_name": "财经金融", "icon": "trending_up"},
            {"category_code": "TECH", "category_name": "科技数码", "icon": "devices"},
            {"category_code": "SOCIAL", "category_name": "社会热点", "icon": "public"},
            {"category_code": "DEVELOPER", "category_name": "开发者", "icon": "code"},
            {"category_code": "VIDEO", "category_name": "视频平台", "icon": "play_circle"},
            {"category_code": "COMMUNITY", "category_name": "社区论坛", "icon": "forum"},
            {"category_code": "KNOWLEDGE", "category_name": "知识问答", "icon": "school"},
        ]}


@app.post("/api/news/list")
async def news_list(req: NewsRequest):
    """获取新闻列表（从VPS同步）"""
    try:
        resp = requests.get(
            f"{NEWS_API_BASE}/news/raw/list",
            params={"page": req.page, "page_size": req.page_size, "category": req.category, "days": 7},
            timeout=15
        )
        data = resp.json()
        # 转换为前端格式
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
        return {"news": news, "category": req.category, "total": data.get("total", 0)}
    except Exception as e:
        return {"news": [], "error": str(e)}


# ========== 其他 API ==========

@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/api/convert")
async def convert(req: ConvertRequest):
    tmp_md = "/tmp/draftbox_input.md"
    with open(tmp_md, "w", encoding="utf-8") as f:
        f.write(req.markdown)
    subprocess.run(["wewrite", "preview", tmp_md, "-t", req.theme, "-o", "/tmp/draftbox_output.html", "--no-open"], timeout=30)
    if os.path.exists("/tmp/draftbox_output.html"):
        with open("/tmp/draftbox_output.html", encoding="utf-8") as f:
            return {"html": f.read(), "theme": req.theme}
    return {"error": "转换失败"}


@app.get("/api/themes")
async def themes():
    themes_dir = Path(__file__).parent.parent / "src" / "wewrite" / "src" / "wewrite" / "toolkit" / "themes"
    if themes_dir.exists():
        return {"themes": [{"id": f.stem, "name": f.stem} for f in themes_dir.glob("*.yaml")]}
    return {"themes": []}


@app.post("/api/grammar/check")
async def grammar_check(req: GrammarCheckRequest):
    try:
        url = "https://api.languagetool.org/v2/check"
        data = {"text": req.text, "language": req.language}
        response = requests.post(url, data=data, timeout=10)
        result = response.json()
        return {"matches": result.get("matches", []), "total": len(result.get("matches", []))}
    except Exception as e:
        return {"error": str(e), "matches": [], "total": 0}


@app.post("/api/images/search")
async def image_search(req: ImageSearchRequest):
    config = load_config()
    pexels_key = config.get("search", {}).get("pexels_key", "")
    if pexels_key:
        try:
            url = f"https://api.pexels.com/v1/search?query={req.query}&per_page={req.count}"
            headers = {"Authorization": pexels_key}
            response = requests.get(url, headers=headers, timeout=10)
            data = response.json()
            images = [{"id": img["id"], "url": img["src"]["large"], "thumb": img["src"]["medium"],
                       "alt": img.get("alt", ""), "author": img["photographer"], "source": "pexels"}
                      for img in data.get("photos", [])]
            return {"images": images, "source": "pexels"}
        except:
            pass
    return {"images": [], "error": "未配置图片搜索 API"}


@app.get("/api/drafts")
async def list_drafts():
    return {"drafts": [{"filename": f.name, "title": f.stem} for f in DRAFTS_DIR.glob("*.md")]}

@app.post("/api/drafts")
async def save_draft(req: DraftSaveRequest):
    import re
    safe = re.sub(r'[<>:"/\\|?*]', "_", req.title)[:50]
    (DRAFTS_DIR / f"{safe}.md").write_text(req.content, encoding="utf-8")
    return {"ok": True}

@app.get("/api/drafts/{filename}")
async def get_draft(filename: str):
    path = DRAFTS_DIR / filename
    if not path.exists(): raise HTTPException(404)
    return {"content": path.read_text(encoding="utf-8")}

@app.delete("/api/drafts/{filename}")
async def delete_draft(filename: str):
    path = DRAFTS_DIR / filename
    if path.exists(): path.unlink()
    return {"ok": True}
