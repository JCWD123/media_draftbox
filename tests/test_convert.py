"""
转换服务测试 - 视频卡片渲染 / 防泄露
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from service.convert import render_video_cards, render_video_card, convert_premium


def test_render_video_card_no_video_tag():
    card = {"path": "/media/videos/a.mp4", "cover": "/media/covers/a.jpg", "caption": "演示视频", "link": "https://example.com/v"}
    html = render_video_card(card)
    assert "<video" not in html
    assert "<iframe" not in html
    assert "▶" in html
    assert "/media/covers/a.jpg" in html
    assert "演示视频" in html
    assert html.startswith("<figure")


def test_render_video_cards_replaces_markers():
    html_in = "<p>正文</p>\n@VIDEO_CARD(1)\n<p>结尾</p>"
    cards = {1: {"path": "/media/videos/a.mp4", "cover": "/media/covers/a.jpg", "caption": "演示", "link": ""}}
    out = render_video_cards(html_in, cards)
    assert "@VIDEO_CARD" not in out
    assert "演示" in out


def test_render_video_cards_missing_card_fallback():
    html_in = "x @VIDEO_CARD(9) y"
    out = render_video_cards(html_in, {})
    assert "@VIDEO_CARD" not in out
    assert "不可用" in out


def test_render_video_card_escapes_caption():
    card = {"path": "/m/v.mp4", "cover": "", "caption": '<script>alert(1)</script>', "link": ""}
    html = render_video_card(card)
    assert "<script>" not in html
    assert "&lt;script&gt;" in html


# ---- 精品排版引擎（学长十一风格）----

PREMIUM_MD = (
    "# 标题示例\n\n"
    "这是正文段落。\n\n"
    "## 二级标题\n\n"
    "> 这是一段引用\n\n"
    "| 指标 | 数值 |\n"
    "|------|------|\n"
    "| 结果 | 10 |\n"
)


def test_premium_render_core_styles():
    html = convert_premium(PREMIUM_MD)["html"]
    # 650 限宽
    assert "max-width:650px" in html
    # 2 倍行高（阅读舒适）
    assert "line-height:2" in html
    # 深蓝强调（h2 左竖线）
    assert "#1f4ed8" in html
    # 标题深蓝近黑
    assert "#172033" in html
    # 全文内联样式（微信兼容，无 <style>）
    assert "<style" not in html
    # 引用块
    assert "<blockquote" in html


def test_premium_render_includes_content():
    html = convert_premium(PREMIUM_MD)["html"]
    assert "标题示例" in html
    assert "二级标题" in html
    assert "这是一段引用" in html
    # 统计卡片表格 → section 卡片
    assert "<section" in html
    assert "10" in html


def test_premium_render_escapes_script():
    md = "# 标题\n\n<script>alert(1)</script>"
    html = convert_premium(md)["html"]
    assert "<script>" not in html
    assert "&lt;script&gt;" in html


def test_premium_shell_wraps_in_section():
    html = convert_premium("# 标题")["html"]
    assert html.strip().startswith("<section")
    assert html.strip().endswith("</section>")
