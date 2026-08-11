"""
质量门禁 - 排版合规校验 + 防泄露（无感自进化核心之一）
每次生成后自动扫描，违规自动降级/修复，教训增量沉淀进 skill
"""
import re
from dataclasses import dataclass, field
from typing import Dict, List

# 检查表: (名称, 正则, 修复说明)
GATE_CHECKS = [
    # 占位符残留（媒体生成失败未替换）
    ("占位符残留", r"\[(IMG|VID):", "图片位用 Pexels 兜底图 / 视频位用文字卡片"),
    # 裸媒体标签（微信不兼容，且泄露代码）
    ("裸媒体标签", r"<(video|iframe|embed|object)\b", "视频位改为说明卡片"),
    # 图片缺 src
    ("图片缺src", r"<img(?![^>]*\bsrc=)", "补兜底图"),
    # 危险脚本（XSS）
    ("危险脚本", r"javascript:|on\w+\s*=", "移除危险属性"),
    # 未渲染的 markdown 图片语法泄露（![...](...) 原样出现在 HTML）
    ("裸markdown图片", r"!\[[^\]]*\]\([^)]*\)", "替换为已生成图片或兜底图"),
    # 未渲染的 @VIDEO_CARD 标记残留
    ("视频标记残留", r"@VIDEO_CARD", "渲染为视频卡片或说明卡片"),
]


@dataclass
class GateResult:
    """门禁结果"""

    ok: bool = True
    issues: List[str] = field(default_factory=list)
    fixed_html: str = ""
    lessons: List[str] = field(default_factory=list)  # 沉淀进 skill 的教训


def run_gate(html: str, fallback_image_url: str = "") -> GateResult:
    """扫描最终 HTML，违规自动修复。返回修复后的 html 与教训列表。"""
    result = GateResult(fixed_html=html)

    # 1. 危险脚本直接移除
    if re.search(r"javascript:|on\w+\s*=", html, re.IGNORECASE):
        result.fixed_html = re.sub(r"(?i)javascript:[^\"'\s>]*", "", result.fixed_html)
        result.fixed_html = re.sub(r"(?i)\son\w+\s*=\s*(\"[^\"]*\"|'[^']*'|[^\s>]+)", "", result.fixed_html)
        result.issues.append("危险脚本")
        result.lessons.append("formatting: 生成内容禁止包含脚本/事件属性")

    # 2. 裸媒体标签降级为说明卡片
    if re.search(r"<(video|iframe|embed|object)\b", result.fixed_html, re.IGNORECASE):
        result.fixed_html = re.sub(
            r"<(video|iframe|embed|object)\b[^>]*>.*?</\1>|<(video|iframe|embed|object)\b[^>]*/?>",
            _video_fallback_card,
            result.fixed_html,
            flags=re.IGNORECASE | re.DOTALL,
        )
        result.issues.append("裸媒体标签")
        result.lessons.append("media: 视频必须走 @VIDEO_CARD 卡片流程，禁止裸 <video> 标签")

    # 3. 占位符残留
    if re.search(r"\[(IMG|VID):", result.fixed_html):
        # 图片位 → 兜底图（若有）；否则移除占位符文本
        if fallback_image_url:
            result.fixed_html = re.sub(r"\[IMG:[^\]]*\]", f'<img src="{fallback_image_url}" style="max-width:100%;"/>', result.fixed_html)
        else:
            result.fixed_html = re.sub(r"\[(IMG|VID):[^\]]*\]", "", result.fixed_html)
        result.issues.append("占位符残留")
        result.lessons.append("media: 媒体占位符必须在渲染前全部替换，残留说明生成失败需兜底")

    # 4. 图片缺 src → 移除（避免破图）
    if re.search(r"<img(?![^>]*\bsrc=)", result.fixed_html, re.IGNORECASE):
        result.fixed_html = re.sub(r"<img(?![^>]*\bsrc=)[^>]*>", "", result.fixed_html, flags=re.IGNORECASE)
        result.issues.append("图片缺src")
        result.lessons.append("formatting: <img> 必须带 src，缺失直接移除避免破图")

    # 5. 裸 markdown 图片语法（![]() 原样出现在 HTML）
    if re.search(r"!\[[^\]]*\]\([^)]*\)", result.fixed_html):
        if fallback_image_url:
            result.fixed_html = re.sub(r"!\[[^\]]*\]\([^)]*\)", f'<img src="{fallback_image_url}" style="max-width:100%;"/>', result.fixed_html)
        else:
            result.fixed_html = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", result.fixed_html)
        result.issues.append("裸markdown图片")
        result.lessons.append("formatting: markdown 图片必须经渲染管线，禁止原样泄露到 HTML")

    # 6. @VIDEO_CARD 标记残留 → 说明卡片
    if "@VIDEO_CARD" in result.fixed_html:
        result.fixed_html = re.sub(
            r"@VIDEO_CARD\([^)]*\)",
            '<div style="padding:16px;background:#f6f8fa;border-radius:8px;text-align:center;color:#888;font-size:14px;">视频（生成中或不可用）</div>',
            result.fixed_html,
        )
        result.issues.append("视频标记残留")
        result.lessons.append("media: 视频卡片必须在渲染阶段替换，残留说明视频生成失败")

    result.ok = len(result.issues) == 0
    return result


def apply_lessons(skill, result: GateResult):
    """门禁教训增量沉淀进 skill（无感进化）"""
    if not result.lessons or skill is None:
        return []
    changes = []
    for lesson in result.lessons:
        if lesson not in skill.raw_text:  # 去重
            skill.raw_text += f"\n{lesson}"
            changes.append(lesson)
    return changes


def _video_fallback_card(match) -> str:
    return (
        '<div style="padding:16px;background:#f6f8fa;border-radius:8px;text-align:center;'
        'color:#888;font-size:14px;">视频内容（该平台不支持内嵌播放）</div>'
    )
