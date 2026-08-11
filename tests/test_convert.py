"""
转换服务测试 - 视频卡片渲染 / 防泄露
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from service.convert import render_video_cards, render_video_card


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
