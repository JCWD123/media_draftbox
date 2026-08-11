"""
Jina API - 搜索 + 正文抓取
- s.jina.ai/query : 付费搜索 + 正文（一个请求返回 搜索结果 + 完整原文）
- r.jina.ai/URL   : 免费阅读器抓正文
- 付费 key 从 ~/.draftbox/config.yaml 的 search.jina_key 读取（仓库外，安全）
"""
import os
import re
import threading
import requests
from pathlib import Path

JINA_READER_BASE = "https://r.jina.ai"
JINA_SEARCH_BASE = "https://s.jina.ai"
_TIMEOUT = 20  # 单次请求超时（秒）
_MAX_BODY = 2000  # 正文截断长度（字符，写给 LLM 用，比 reader 长些）

_RL_LOCK = threading.Lock()

# 真实浏览器 UA（Jina 拦截默认 Python-UA → 403）
_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36"


def _get_config():
    """读取~/.draftbox/config.yaml（若存在）"""
    cfg_file = Path.home() / ".draftbox" / "config.yaml"
    try:
        import yaml
        cfg = yaml.safe_load(open(cfg_file, encoding="utf-8")) or {}
        search_cfg = cfg.get("search", {}) or {}
        return {
            "jina_key": search_cfg.get("jina_key", ""),
            "jina_enabled": search_cfg.get("jina_enabled", bool(search_cfg.get("jina_key"))),
        }
    except Exception:
        return {"jina_key": "", "jina_enabled": False}


def jina_key_available() -> bool:
    """是否配置了付费 Jina key"""
    return bool(_get_config().get("jina_key"))


def search_web(query: str, limit: int = 8) -> dict:
    """付费 Jina 搜索（s.jina.ai）：一个请求返回 搜索结果 + 完整正文

    返回 {news: [{id,title,summary,link,published,source,category}], total, error}
    """
    cfg = _get_config()
    key = cfg.get("jina_key", "")
    if not key:
        return {"news": [], "total": 0, "error": "未配置 Jina key（search.jina_key）"}

    with _RL_LOCK:
        url = f"{JINA_SEARCH_BASE}/{requests.utils.requote_uri(query)}"
        try:
            resp = requests.get(url, headers={
                "Authorization": f"Bearer {key}",
                "User-Agent": _UA,
            }, timeout=_TIMEOUT)
            if resp.status_code != 200:
                return {"news": [], "total": 0, "error": f"Jina 搜索失败 HTTP {resp.status_code}"}
            # ⚠️ 必须用 resp.content.decode('utf-8') 而非 resp.text
            # Jina 响应头未声明 charset，requests 的 resp.text 默认 ISO-8859-1(Latin-1) 解码，
            # UTF-8 中文会变乱码（如 "AIè§喍é¢çæå¨"）。显式 UTF-8 解码修复。
            html = resp.content.decode("utf-8", errors="ignore")
        except Exception as e:
            return {"news": [], "total": 0, "error": f"Jina 搜索失败: {str(e)[:80]}"}

    # 解析 [n] 字段结构（同序号为一结果）
    import hashlib
    news = []
    cur = {}
    cur_idx = None
    for line in html.split("\n"):
        m = re.match(r"^\[(\d+)\]\s*(.*)$", line.strip())
        if m:
            idx = int(m.group(1))
            rest = m.group(2).strip()
            if idx != cur_idx and cur:
                news.append(cur)
                cur, cur_idx = {"idx": idx}, idx
            elif idx != cur_idx:
                cur, cur_idx = {"idx": idx}, idx
            fm = re.match(r"^(Title|URL Source|Description|Published Time)\s*:\s*(.*)$", rest)
            if fm:
                cur[fm.group(1)] = fm.group(2).strip()
            else:
                cur.setdefault("body_lines", []).append(rest)
        elif cur is not None:
            cur.setdefault("body_lines", []).append(line)
    if cur:
        news.append(cur)

    out = []
    seen = set()
    for item in news:
        title = item.get("Title", "")
        url = item.get("URL Source", "")
        if not title or not url or url in seen:
            continue
        seen.add(url)
        # 正文清理：过滤图片行 / Date / 纯链接导航 / 残留字段头 / 视频页导航词
        body_lines = item.get("body_lines", [])
        _NAV_WORDS = ("back", "skip navigation", "tap to unmute", "log in", "登录", "搜索",
                      "search with your voice", "home", "sign up", "注册", "menu", "more",
                      "share", "watch on", "settings", "back to", "this is a video")
        cleaned = []
        for ln in body_lines:
            s = ln.strip()
            low = s.lower()
            if not s:
                continue
            # 跳过 Jina 残留元数据 / 图片 / 纯链接导航
            if re.match(r"^(Title|URL Source|Description|Published Time|Date)\s*:\s*", s):
                continue
            if re.match(r"^!\[[^\]]*\]\([^)]*\)$", s) or re.match(r"^\[\]\([^)]*\)$", s):
                continue
            if re.match(r"^(\[[^\]]*\]\([^)]*\)\s*)+$", s) or re.match(r"^\s*\*\s*\[[^\]]*\]\([^)]*\)\s*$", s):
                continue
            # 跳过纯导航/视频UI词
            if low.rstrip("，。,.") in _NAV_WORDS or s in ("Back", "Skip navigation"):
                continue
            cleaned.append(s)
        body = re.sub(r"\n{3,}", "\n\n", "\n".join(cleaned)).strip()
        if len(body) > _MAX_BODY:
            body = body[:_MAX_BODY] + "……（已截断）"
        desc = item.get("Description", "")
        nid = hashlib.md5(url.encode("utf-8")).hexdigest()[:8]
        out.append({
            "id": nid,
            "title": title,
            "summary": (body or desc)[:400],  # 正文优先，其次描述
            "link": url,
            "published": (item.get("Published Time") or "")[:10],
            "source": re.search(r"https?://([^/]+)", url).group(1) if re.search(r"https?://([^/]+)", url) else "Jina",
            "category": "SEARCH",
            "_backend": "jina",
        })
        if len(out) >= limit:
            break
    return {"news": out, "total": len(out), "error": ""}


def fetch_article(url: str) -> dict:
    """用 Jina Reader 抓取单个 URL 的正文

    返回 {ok, title, body, error}
    """
    if not url or not url.startswith("http"):
        return {"ok": False, "body": "", "title": "", "error": "无效 URL"}

    with _RL_LOCK:
        target = f"{JINA_READER_BASE}/{url}"
        try:
            resp = requests.get(
                target,
                headers={"Accept": "text/markdown, text/plain"},
                timeout=_TIMEOUT,
            )
            if resp.status_code != 200:
                return {"ok": False, "body": "", "title": "", "error": f"抓取失败 HTTP {resp.status_code}"}
            text = resp.content.decode("utf-8", errors="ignore")
        except Exception as e:
            return {"ok": False, "body": "", "title": "", "error": f"抓取失败: {str(e)[:80]}"}

    title = ""
    m = re.search(r"^Title:\s*(.+)$", text, re.M)
    if m:
        title = m.group(1).strip()

    body = _extract_body(text)
    # 二次清理：合并空行，截断
    if len(body) > _MAX_BODY:
        body = body[:_MAX_BODY] + "……（已截断）"

    if not body and not title:
        return {"ok": False, "body": "", "title": "", "error": "未提取到内容"}

    return {"ok": True, "title": title, "body": body, "error": ""}


def fetch_articles(urls: list, max_items: int = 5) -> dict:
    """抓取多个 URL 正文（供勾选的多条新闻）"""
    results = {}
    for url in urls[:max_items]:
        res = fetch_article(url)
        if res["ok"]:
            results[url] = {"title": res["title"], "body": res["body"]}
    return results
