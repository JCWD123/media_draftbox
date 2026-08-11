"""
AI 写作服务 - 三模态编排（文字 + 图片 + 视频）

流程: 规划(占位符+标签) → 文字 → 图片(Seedream/Pexels兜底) → 视频(后台) → 渲染 → 门禁 → 垂直度
"""
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from utils.llm import llm_chat, strip_markdown_code_block
from skill_core.store import SkillStore
from skill_core.builder import build_plan_prompt
from skill_core.gate import run_gate, apply_lessons
from skill_core.vertical import check_vertical
from service.news import fetch_news_by_ids
from service.images import search_images
from service import convert
from service import media_task

IMG_PATTERN = re.compile(r"\[IMG:\s*(.*?)\]", re.DOTALL)
VID_PATTERN = re.compile(r"\[VID:\s*(.*?)\]", re.DOTALL)


def _gen_id() -> str:
    return "gen_" + datetime.now().strftime("%Y%m%d_%H%M%S")


# ---------------------------------------------------------------
# 解析
# ---------------------------------------------------------------

def parse_article(raw: str, max_images: int = 4, max_videos: int = 1) -> Dict:
    """解析 LLM 输出：标题 / 正文 / 占位符截断 / 标签提取"""
    text = strip_markdown_code_block(raw)
    if not text:
        return {"ok": False, "error": "模型返回为空"}

    lines = text.splitlines()
    title = ""
    body_lines = []
    tags: List[str] = []
    for line in lines:
        s = line.strip()
        if not title and s.startswith("# ") and len(s) > 2:
            title = s[2:].strip()
            continue
        if s.startswith("标签:") or s.startswith("标签："):
            tag_str = s.split(":", 1)[1] if ":" in s else s.split("：", 1)[1]
            tags = [t.strip() for t in re.split(r"[，,、;；]", tag_str) if t.strip()]
            continue
        body_lines.append(line)

    content = "\n".join(body_lines).strip()
    img_count = {"n": 0}
    vid_count = {"n": 0}

    # 图片占位符截断到 max_images（超出删除）
    if max_images <= 0:
        content = IMG_PATTERN.sub("", content)
    else:
        def _limit_img(m):
            img_count["n"] += 1
            return m.group(0) if img_count["n"] <= max_images else ""

        content = IMG_PATTERN.sub(_limit_img, content)

    # 视频占位符：不生成视频时全部删除
    if max_videos <= 0:
        content = VID_PATTERN.sub("", content)
    else:
        def _limit_vid(m):
            vid_count["n"] += 1
            return m.group(0) if vid_count["n"] <= max_videos else ""

        content = VID_PATTERN.sub(_limit_vid, content)

    return {
        "ok": True,
        "title": title,
        "content": content,
        "tags": tags[:5],
        "img_count": img_count["n"],
        "vid_count": vid_count["n"],
    }


# ---------------------------------------------------------------
# 图片生成
# ---------------------------------------------------------------

def generate_images(markdown: str, max_images: int, draft_id: str):
    """为 [IMG: 描述] 生成图片；失败走 Pexels 兜底。返回 (新markdown, media列表, warnings)"""
    media: List[Dict] = []
    warnings: List[str] = []
    if max_images <= 0 or "[IMG:" not in markdown:
        return markdown, media, warnings

    from providers import get_image
    provider = get_image()  # 未配置 key 时 generate 抛可读错误

    n = {"n": 0}

    def _repl(m):
        n["n"] += 1
        desc = m.group(1).strip()
        try:
            data = provider.generate(desc, "1920x1080")
            path = media_task.IMAGES_DIR / f"{draft_id}_{n['n']}.png"
            path.write_bytes(data)
            url = f"/media/images/{path.name}"
            media.append({"idx": n["n"], "path": url, "alt": desc[:80], "source": "seedream"})
            return f"\n![{desc[:60]}]({url})\n"
        except Exception as e:
            fallback = _pexels_fallback(desc)
            if fallback:
                media.append({"idx": n["n"], "path": fallback, "alt": desc[:80], "source": "pexels"})
                return f"\n![{desc[:60]}]({fallback})\n"
            warnings.append(f"图片 {n['n']} 生成失败: {str(e)[:100]}（保留占位符，门禁兜底）")
            return m.group(0)  # 保留占位符，由门禁降级

    markdown = IMG_PATTERN.sub(_repl, markdown, count=max_images)
    return markdown, media, warnings


def _pexels_fallback(desc: str) -> str:
    """Pexels 兜底图（提取描述关键词搜索一张）"""
    try:
        kw = re.sub(r"[，,。.、：:；;（）()\"'“”\s]+", " ", desc).strip()[:20]
        result = search_images(kw, 1)
        imgs = result.get("images", [])
        if imgs:
            return imgs[0]["url"]
    except Exception:
        pass
    return ""


# ---------------------------------------------------------------
# 视频后台完成回调
# ---------------------------------------------------------------

def _finalize_videos(draft_id: str):
    """视频后台生成完成后：渲染视频卡片进 HTML，跑门禁，记录"""
    try:
        status = media_task.get_video_status(draft_id)
        if status.get("status") != "done":
            return
        videos = status.get("videos", [])
        video_cards = {v["idx"]: v for v in videos}
        markdown = media_task.get_task_markdown(draft_id)
        if markdown is None:
            return
        html_result = convert.convert_markdown(markdown, "professional-clean", video_cards=video_cards)
        if html_result.get("error"):
            return
        html = html_result["html"]
        # 门禁
        gate = run_gate(html)
        if not gate.ok:
            html = gate.fixed_html
            store = SkillStore()
            skill = store.load("wechat-writing") or store.load_default()
            lessons = apply_lessons(skill, gate)
            if lessons:
                store.append_evolution(skill.name, {"type": "gate", "issues": gate.issues, "lessons": lessons})
                store.bump_version(skill)
        media_task.set_final_html(draft_id, html)
        store = SkillStore()
        skill = store.load("wechat-writing") or store.load_default()
        store.save_generation(skill.name, {"draft_id": draft_id, "type": "video_done", "videos": videos})
    except Exception:
        pass  # 后台回调失败不阻塞主流程


# ---------------------------------------------------------------
# 主入口
# ---------------------------------------------------------------

def generate_article(req) -> Dict:
    """三模态生成主入口"""
    if not req.topic or not req.topic.strip():
        return {"success": False, "error": "请提供核心思路/话题"}

    store = SkillStore()
    skill_name = getattr(req, "skill_name", "") or "wechat-writing"
    skill = store.load(skill_name) or store.load_default()

    # 新闻素材
    news_items = []
    if getattr(req, "news_ids", None):
        news_items = fetch_news_by_ids(req.news_ids)

    # 1. 规划 + 文字生成
    try:
        messages = build_plan_prompt(
            skill,
            req.topic.strip(),
            news_items,
            getattr(req, "upload_content", "") or "",
            getattr(req, "title", "") or "",
            req.max_images,
            req.max_videos,
        )
        raw = llm_chat(messages)
    except (ValueError, RuntimeError, TimeoutError) as e:
        return {"success": False, "error": str(e)}

    parsed = parse_article(raw, req.max_images, req.max_videos)
    if not parsed["ok"]:
        return {"success": False, "error": parsed["error"]}

    draft_id = _gen_id()
    markdown = parsed["content"]
    title = (getattr(req, "title", "") or "").strip() or parsed["title"] or f"未命名文章"
    media: Dict = {"images": [], "videos": []}
    warnings: List[str] = []

    # 2. 图片生成
    if req.with_images:
        markdown, media["images"], img_warnings = generate_images(markdown, req.max_images, draft_id)
        warnings.extend(img_warnings)

    # 3. 视频 → 后台任务（先替换占位符为 @VIDEO_CARD(n)）
    video_pending = False
    if req.with_video and req.max_videos > 0:
        vids = VID_PATTERN.findall(markdown)
        if vids:
            video_specs = [{"idx": i + 1, "prompt": v.strip()} for i, v in enumerate(vids[:req.max_videos])]
            it = iter(video_specs)

            def _v_repl(m):
                spec = next(it, None)
                return f"@VIDEO_CARD({spec['idx']})" if spec else ""

            markdown = VID_PATTERN.sub(_v_repl, markdown, count=req.max_videos)
            media_task.set_task_markdown(draft_id, markdown)
            media_task.enqueue_video_generation(draft_id, video_specs, on_done=_finalize_videos)
            video_pending = True

    # 4. 渲染 HTML（视频卡片为空 dict：占位符先以"不可用卡片"呈现，后台完成后刷新）
    html_result = convert.convert_markdown(markdown, "professional-clean", video_cards={})
    if html_result.get("error"):
        return {"success": False, "error": html_result["error"]}
    html = html_result["html"]

    # 5. 质量门禁
    gate = run_gate(html)
    if not gate.ok:
        html = gate.fixed_html
        lessons = apply_lessons(skill, gate)
        if lessons:
            store.append_evolution(skill.name, {"type": "gate", "issues": gate.issues, "lessons": lessons})
            store.bump_version(skill)

    # 6. 垂直度
    vertical_result = check_vertical(parsed["tags"], skill)
    if vertical_result.drifted:
        store.append_evolution(skill.name, {
            "type": "vertical",
            "tags": parsed["tags"],
            "note": vertical_result.note,
            "suggestion": vertical_result.suggestion,
        })

    # 7. 记录 + use_count
    store.save_generation(skill.name, {
        "draft_id": draft_id,
        "title": title,
        "tags": parsed["tags"],
        "media": media,
        "warnings": warnings,
        "video_pending": video_pending,
    })
    store.update_meta(skill, use_count=int(skill.meta.get("use_count", 0)) + 1)

    return {
        "success": True,
        "content": markdown,
        "html": html,
        "title": title,
        "tags": parsed["tags"],
        "vertical_check": {
            "domain": vertical_result.domain,
            "drifted": vertical_result.drifted,
            "note": vertical_result.note or vertical_result.suggestion,
        },
        "media": media,
        "warnings": warnings,
        "skill_version": skill.version,
        "draft_id": draft_id,
        "video_pending": video_pending,
    }


def media_status(draft_id: str) -> Dict:
    """视频任务状态查询（前端轮询）"""
    status = media_task.get_video_status(draft_id)
    html = media_task.get_final_html(draft_id)
    return {"success": True, **status, "html": html}
