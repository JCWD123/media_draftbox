"""
无感进化引擎 - 目标自动学习（作者零操作，后台自动进化）

- targets: ~/.draftbox/targets.json（学习目标公众号列表）
- 已学 URL 去重: ~/.draftbox/skills/learned_urls.json
- auto_learn_once: 定时任务调用，抓取 targets 新文章 → 自动学习
"""
import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from skill_core.store import SkillStore
from skill_core.analyzer import learn_from_article

TARGETS_FILE = Path.home() / ".draftbox" / "targets.json"
LEARNED_URLS_FILE = Path.home() / ".draftbox" / "skills" / "learned_urls.json"

_lock = threading.Lock()


# ---------------- 学习目标 ----------------

def load_targets() -> List[Dict]:
    if TARGETS_FILE.exists():
        try:
            return json.loads(TARGETS_FILE.read_text(encoding="utf-8")) or []
        except Exception:
            return []
    return []


def save_targets(targets: List[Dict]):
    TARGETS_FILE.parent.mkdir(parents=True, exist_ok=True)
    TARGETS_FILE.write_text(json.dumps(targets, ensure_ascii=False, indent=1), encoding="utf-8")


def add_target(name: str, url: str, weight: int = 1) -> Dict:
    with _lock:
        targets = load_targets()
        for t in targets:
            if t.get("url") == url:
                return {"success": False, "error": "该目标已存在"}
        targets.append({"name": name, "url": url, "weight": weight, "added": datetime.now().strftime("%Y-%m-%d")})
        save_targets(targets)
    return {"success": True, "targets": targets}


def remove_target(url: str) -> Dict:
    with _lock:
        targets = [t for t in load_targets() if t.get("url") != url]
        save_targets(targets)
    return {"success": True, "targets": targets}


# ---------------- 已学 URL 去重 ----------------

def _load_learned() -> set:
    if LEARNED_URLS_FILE.exists():
        try:
            return set(json.loads(LEARNED_URLS_FILE.read_text(encoding="utf-8")))
        except Exception:
            return set()
    return set()


def _mark_learned(url: str):
    learned = _load_learned()
    learned.add(url)
    LEARNED_URLS_FILE.parent.mkdir(parents=True, exist_ok=True)
    LEARNED_URLS_FILE.write_text(json.dumps(sorted(learned), ensure_ascii=False), encoding="utf-8")


# ---------------- 自动学习 ----------------

def auto_learn_once(skill_name: str = "wechat-writing", per_target: int = 5) -> Dict:
    """
    抓取所有学习目标的新文章并自动学习（定时任务调用）。
    只处理未学过的 URL；失败（反爬等）静默跳过，下次再试。
    """
    from service.wechat_fetcher import fetch_url

    targets = load_targets()
    if not targets:
        return {"success": True, "learned": 0, "message": "无学习目标"}

    store = SkillStore()
    learned = _load_learned()
    total_learned = 0
    errors = 0

    for target in targets:
        url = target.get("url", "")
        if not url or not url.startswith("http"):
            continue
        # 简化：目标 URL 视为文章列表页或单篇文章。单篇处理，列表页抓取失败静默。
        if url in learned:
            continue
        article = fetch_url(url)
        if not article:
            errors += 1
            continue
        result = learn_from_article(store, skill_name, article["title"], article["content"], source=url)
        if result.get("success"):
            _mark_learned(url)
            if result.get("learned"):
                total_learned += 1
        per_target -= 1
        if per_target <= 0:
            break

    return {"success": True, "learned": total_learned, "errors": errors}
