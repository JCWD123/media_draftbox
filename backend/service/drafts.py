"""
草稿管理服务
"""
import re
from pathlib import Path

DRAFTS_DIR = Path.home() / ".draftbox" / "drafts"
DRAFTS_DIR.mkdir(parents=True, exist_ok=True)


def list_drafts():
    """列出草稿"""
    return {"drafts": [{"filename": f.name, "title": f.stem} for f in DRAFTS_DIR.glob("*.md")]}


def save_draft(title: str, content: str):
    """保存草稿"""
    safe = re.sub(r'[<>:"/\\|?*]', "_", title)[:50]
    (DRAFTS_DIR / f"{safe}.md").write_text(content, encoding="utf-8")
    return {"ok": True}


def get_draft(filename: str):
    """获取草稿"""
    path = DRAFTS_DIR / filename
    if not path.exists():
        return None
    return {"content": path.read_text(encoding="utf-8")}


def delete_draft(filename: str):
    """删除草稿"""
    path = DRAFTS_DIR / filename
    if path.exists():
        path.unlink()
    return {"ok": True}
