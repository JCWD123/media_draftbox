"""
草稿管理服务
- 草稿以结构化 JSON 存储：{ title, markdown, html, updated_at }
- markdown: 源文件（可回编辑）
- html: wewrite 排版后的微信兼容 HTML（可直接复制发布）
"""
import json
import re
from datetime import datetime
from pathlib import Path

DRAFTS_DIR = Path.home() / ".draftbox" / "drafts"
DRAFTS_DIR.mkdir(parents=True, exist_ok=True)

# 草稿文件后缀
EXT = ".json"


def _safe_filename(title: str) -> str:
    """清洗标题为安全文件名"""
    safe = re.sub(r'[<>:"/\\|?*]', "_", title).strip()
    return safe[:50] or "未命名"


def list_drafts():
    """列出草稿（返回标题 + 时间戳）"""
    drafts = []
    for f in sorted(DRAFTS_DIR.glob(f"*{EXT}"), key=lambda x: x.stat().st_mtime, reverse=True):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            drafts.append({
                "filename": f.name,
                "title": data.get("title", f.stem),
                "updated_at": data.get("updated_at", ""),
            })
        except Exception:
            continue
    return {"drafts": drafts}


def save_draft(title: str, content: str, html: str = ""):
    """保存草稿
    title:   草稿标题
    content: markdown 源内容
    html:    wewrite 排版后的 HTML（可选，存 HTML 供直接复制发布）
    """
    safe = _safe_filename(title)
    path = DRAFTS_DIR / f"{safe}{EXT}"
    # 若文件已存在但标题不同（同名覆盖），追加时间戳避免误覆盖
    if path.exists() and path.read_text(encoding="utf-8").find(f'"title": "{title}"') < 0:
        safe = f"{safe}_{datetime.now().strftime('%H%M%S')}"
        path = DRAFTS_DIR / f"{safe}{EXT}"
    data = {
        "title": title,
        "markdown": content,
        "html": html,
        "updated_at": datetime.now().isoformat(timespec="seconds"),
    }
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"ok": True, "filename": path.name}


def get_draft(filename: str):
    """获取草稿（返回 markdown + html）"""
    path = DRAFTS_DIR / filename
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return {
        "title": data.get("title", ""),
        "markdown": data.get("markdown", ""),
        "html": data.get("html", ""),
        "updated_at": data.get("updated_at", ""),
    }


def delete_draft(filename: str):
    """删除草稿"""
    path = DRAFTS_DIR / filename
    if path.exists():
        path.unlink()
    return {"ok": True}
