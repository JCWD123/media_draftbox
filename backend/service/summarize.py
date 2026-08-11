"""
新闻 AI 摘要服务
- 优先用已有正文/摘要(summary)喂 LLM 提炼核心摘要
- 正文不足时用 Jina Reader 抓原文兜底
- 都没有则仅按标题概括（仍给出大致方向）
"""
from utils.llm import llm_chat, strip_markdown_code_block


def _build_content(title: str, summary: str, link: str) -> tuple:
    """准备输入 LLM 的内容。返回 (内容, 来源说明)"""
    summary = (summary or "").strip()
    if len(summary) >= 30:
        return summary[:2000], "已有正文"
    # 正文不足，尝试 Jina 抓原文
    if link and link.startswith("http"):
        try:
            from tools.jina_reader import fetch_article
            res = fetch_article(link)
            if res.get("ok") and res.get("body") and len(res.get("body", "")) >= 30:
                return res["body"][:2000], "抓取原文"
        except Exception:
            pass
    return title, "仅标题"


def summarize(title: str, summary: str = "", link: str = "") -> dict:
    """对一条新闻生成 AI 核心摘要（50-120 字）"""
    if not title:
        return {"success": False, "error": "缺少新闻标题"}

    content, source = _build_content(title, summary, link)
    if not content.strip():
        return {"success": False, "error": "该新闻无法获取内容进行摘要"}

    prompt = (
        "你是新闻摘要助手。请用一段简洁的核心摘要概括下面这篇新闻，让读者不用点开原文就能知道大致讲了什么。\n"
        "要求：\n"
        "1. 用中文，80-120 字左右，一段话\n"
        "2. 突出事件核心、关键人物/主体、重要数据或结论\n"
        "3. 客观准确，不添加原文没有的信息\n"
        "4. 只输出摘要文本本身，不要任何前缀或格式标记\n\n"
        f"【新闻标题】\n{title}\n\n"
        f"【后续内容】\n{content[:2000]}\n\n"
        "请输出这条新闻的核心摘要："
    )

    try:
        raw = llm_chat([{"role": "user", "content": prompt}], timeout=60)
        result = strip_markdown_code_block(raw or "").strip()
        # 截断保护
        if len(result) > 300:
            result = result[:300]
        if not result:
            return {"success": False, "error": "摘要生成失败(空)"}
        return {"success": True, "summary": result, "source": source}
    except (ValueError, RuntimeError, TimeoutError) as e:
        return {"success": False, "error": str(e)}
