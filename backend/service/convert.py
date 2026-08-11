"""
转换服务 - wewrite 引擎
"""
import html as html_lib
import re
import subprocess
import tempfile
from pathlib import Path

# 主题别名映射：兼容前端历史传值（前端 themeList 里的 id 是旧名）
THEME_ALIASES = {
    "professional": "professional-clean",
}

# 真实主题白名单（与 wewrite 主题文件对齐）
VALID_THEMES = {
    "bauhaus", "bold-green", "bold-navy", "bytedance", "elegant-rose",
    "focus-red", "github", "impeccable", "ink", "lobster-notes",
    "midnight", "minimal", "minimal-gold", "newspaper", "professional-clean",
    "sspai", "tech-modern", "warm-editorial",
}


def resolve_theme(theme: str) -> str:
    """解析主题名（别名 → 真实文件名）"""
    theme = theme.strip()
    if theme in VALID_THEMES:
        return theme
    if theme in THEME_ALIASES:
        resolved = THEME_ALIASES[theme]
        if resolved in VALID_THEMES:
            return resolved
    raise ValueError(f"未知主题: {theme}，可用主题: {sorted(VALID_THEMES)}")


def convert_markdown(markdown: str, theme: str, video_cards: dict = None):
    """Markdown → 微信兼容 HTML

    video_cards: {1: {"path","cover","caption","link"}} —— markdown 中的 @VIDEO_CARD(1)
    标记会被渲染为样式化视频卡片（纯 inline style，无 <video> 标签，微信兼容）。
    """
    if theme == "premium":
        return convert_premium(markdown, video_cards)

    try:
        resolved = resolve_theme(theme)
    except ValueError as e:
        return {"error": str(e)}

    with tempfile.TemporaryDirectory(prefix="draftbox_") as tmp_dir:
        tmp_md = Path(tmp_dir) / "input.md"
        tmp_html = Path(tmp_dir) / "output.html"
        tmp_md.write_text(markdown, encoding="utf-8")

        result = subprocess.run(
            ["wewrite", "preview", str(tmp_md), "-t", resolved, "-o", str(tmp_html), "--no-open"],
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode != 0 or not tmp_html.exists():
            return {
                "error": f"转换失败 (theme={resolved}): {(result.stderr or result.stdout or '').strip()[:300]}"
            }

        html_out = tmp_html.read_text(encoding="utf-8")

    # 视频卡片渲染：@VIDEO_CARD(n) → 样式化卡片（无 <video> 标签，防泄露）
    if video_cards:
        html_out = render_video_cards(html_out, video_cards)
    return {"html": html_out, "theme": resolved}


def render_video_cards(html_out: str, video_cards: dict) -> str:
    """把 @VIDEO_CARD(n) 标记替换为视频卡片 HTML"""
    def _repl(m):
        idx = int(m.group(1))
        card = video_cards.get(idx)
        if not card:
            return ('<div style="padding:16px;background:#f6f8fa;border-radius:8px;text-align:center;'
                    'color:#888;font-size:14px;">视频（不可用）</div>')
        return render_video_card(card)

    return re.sub(r"@VIDEO_CARD\(\s*(\d+)\s*\)", _repl, html_out)


def render_video_card(card: dict) -> str:
    """单个视频卡片 HTML（纯 inline style，微信粘贴兼容，不泄露任何代码）"""
    cover = card.get("cover", "")
    caption = html_lib.escape(card.get("caption", "视频"))
    link = card.get("link") or card.get("path", "")

    if cover:
        img = f'<img src="{cover}" style="width:100%;border-radius:8px;" alt="视频封面"/>'
    else:
        img = ('<div style="width:100%;height:200px;background:#f0f0f0;border-radius:8px;'
               'display:flex;align-items:center;justify-content:center;color:#999;">视频</div>')
    play_btn = ('<span style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);'
                'width:56px;height:56px;border-radius:50%;background:rgba(0,0,0,0.6);'
                'display:flex;align-items:center;justify-content:center;font-size:24px;color:#fff;">▶</span>')
    return (
        f'<figure style="margin:16px 0;text-align:center;">'
        f'<a href="{link}" target="_blank" style="display:block;position:relative;'
        f'border-radius:8px;overflow:hidden;">{img}{play_btn}</a>'
        f'<figcaption style="color:#888;font-size:14px;margin-top:8px;">{caption}</figcaption>'
        f'</figure>'
    )


def get_themes():
    """获取主题列表"""
    # 精品排版主题 + wewrite 主题
    premium_themes = [{"id": "premium", "name": "学长十一·精选"}]
    # 优先读项目内 wewrite 引擎的主题目录，其次读用户目录
    candidates = [
        Path(__file__).parent.parent.parent / "src" / "wewrite" / "src" / "wewrite" / "toolkit" / "themes",
        Path.home() / ".wewrite" / "themes",
    ]
    wewrite_themes = []
    for themes_dir in candidates:
        if themes_dir.exists():
            wewrite_themes = [{"id": f.stem, "name": f.stem} for f in sorted(themes_dir.glob("*.yaml"))]
            break
    if not wewrite_themes:
        wewrite_themes = [{"id": t, "name": t} for t in sorted(VALID_THEMES)]
    return {"themes": premium_themes + wewrite_themes}


def convert_premium(markdown, video_cards=None):
    """精品排版（学长十一风格，内联样式）"""
    from service.premium import render as premium_render
    html_out = premium_render(markdown)
    html_ns = html_out
    if video_cards:
        html_ns = render_video_cards(html_ns, video_cards)
    return {"html": html_ns, "theme": "premium"}
