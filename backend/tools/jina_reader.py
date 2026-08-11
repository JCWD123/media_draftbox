"""
Jina Reader 免费阅读器 - 抓取新闻正文
r.jina.ai/URL 免费把网页正文转成 Markdown，供 AI 写作提炼核心思路
- 无需 API key（免费额度）
- 单次抓取设置超时，避免阻塞写作流程
"""
import re
import threading
import requests

JINA_READER_BASE = "https://r.jina.ai"
_TIMEOUT = 15  # 单条抓取超时（秒）
_MAX_BODY = 1500  # 正文截断长度（字符）

_RL_LOCK = threading.Lock()


# ---- 导航/噪音识别 ----
# 列表导航项：* [链接文字](链接)
_LIST_LINK_RE = re.compile(r"^\s*\*?\s*\[[^\]]*\]\([^)]*\)\s*$")
# Markdown 链接（纯，无 * 前缀）
_MD_LINK_RE = re.compile(r"^\[[^\]]*\]\([^)]*\)\s*$")


def _is_noise_line(s: str) -> bool:
    """判断一行是否属于导航/广告噪音"""
    if not s:
        return True
    # 列表导航（* [首页](url)）
    if _LIST_LINK_RE.match(s):
        return True
    # 纯 markdown 链接
    if _MD_LINK_RE.match(s):
        return True
    # 常见导航词
    if s in ("首页", "资讯", "视频", "直播", "登录", "注册", "站内", "关注", "了解更多") or "站内搜索" in s:
        return True
    # 面包屑（xx > yy > 正文）
    if ">正文" in s or (s.count(">") >= 2 and len(s) < 60):
        return True
    return False


def _extract_body(markdown: str) -> str:
    """从 Jina Reader 返回的 Markdown 中提取正文（去元数据头/导航/图片噪音）"""
    if not markdown:
        return ""

    # 去掉 Jina 元数据头：Title/URL Source/Published/Markdown Content
    # 找到第一个真正的正文起点：跳过前导噪声
    lines = markdown.split("\n")
    keep = []
    started = False
    seen_content = False
    for ln in lines:
        s = ln.strip()
        if not s:
            if started:
                keep.append("")  # 保留正文空行
            continue

        # 跳过 Jina 元数据头行
        if re.match(r"^(Title|URL Source|Published Time|Markdown Content)\s*:", s):
            if s.startswith("Markdown Content"):
                seen_content = True
            continue
        # NOT_AUTO: 跳过 "Markdown Content" 之后的第一个 导航块
        if not started:
            # 图片行（正文开始前的大图）
            if s.startswith("![") or _is_noise_line(s):
                continue
            started = True
        if _is_noise_line(s):
            continue
        keep.append(s)

    body = "\n".join(keep)
    body = re.sub(r"\n{3,}", "\n\n", body).strip()
    return body


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
            text = resp.text
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
