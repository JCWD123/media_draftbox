"""
PromptBuilder - 三模态规划 prompt 组装（skill-core 核心）
优先级: 核心思路 > 上传文件 > 新闻素材 > Skill 风格
"""
from typing import Dict, List


def build_plan_prompt(
    skill,
    topic: str,
    news_items: List[Dict] = None,
    upload_content: str = "",
    title: str = "",
    max_images: int = 4,
    max_videos: int = 1,
) -> List[dict]:
    """组装生成 prompt，返回 [system, user] 消息列表"""
    skill_yaml = skill.raw_text if skill else ""

    news_text = ""
    if news_items:
        lines = []
        for i, item in enumerate(news_items, 1):
            title_ = item.get("title", "")
            link = item.get("link", "")
            source = item.get("source", "")
            summary = (item.get("summary") or "").strip()
            lines.append(f"{i}. {title_}（来源: {source}）{link}")
            # 若有正文/摘要（Jina Reader 抓取或 RSS 摘要），附带供提炼
            if summary:
                lines.append(f"   内容: {summary[:600]}")
        news_text = "\n".join(lines)

    upload_text = f"\n\n【上传的参考文档】\n{upload_content}\n" if upload_content else ""
    title_line = f"\n【指定标题（必须使用）】\n{title}\n" if title else ""

    video_inst = (
        f"- [VID: 视频描述] —— 描述 5-10 秒动态场景，适合文章叙事，最多 {max_videos} 个（仅当内容确实需要时）"
        if max_videos > 0 else "- 本文不插入任何视频占位符"
    )

    system = (
        "你是公众号写作专家，擅长撰写高质量、可读性强的公众号文章。"
        "严格遵守用户提供的写作规范（这是作者通过长期反馈沉淀的风格，不可违背）。"
    )

    user = f"""请写一篇公众号文章。

【写作规范，必须严格遵循】
{skill_yaml}

【作者核心思路，必须严格围绕】
{topic}
{upload_text}{title_line}
【新闻素材，可引用其中的事实和数据】
{news_text if news_text else "（无）"}

【输出要求】
1. 输出 Markdown，用 ## 分节，800-1500 字
2. 标题另起一行以 # 开头（如 # 文章标题）
3. 在文中合适位置插入媒体占位符（禁止插入任何真实图片/视频代码、禁止插入 HTML 标签）：
   - [IMG: 配图描述] —— 描述配图内容、场景、构图、风格，每 2-3 段一个，最多 {max_images} 个
   - {video_inst}
4. 占位符只能出现在段落之间（前后各空一行），不能出现在标题行内或段落中间
5. 严格遵守写作规范中的 style / anti_patterns / media 章节
6. 全文最后一行输出标签行，格式必须为：标签: 标签1, 标签2, 标签3（2-5 个，与内容垂直度强相关）
"""

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
