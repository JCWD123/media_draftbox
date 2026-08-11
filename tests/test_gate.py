"""
质量门禁测试 - 5 类检查项 / 降级修复 / 教训沉淀
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from skill_core.gate import run_gate, apply_lessons
from skill_core.store import SkillStore


def test_gate_detects_placeholder_residue():
    html = '<p>正文</p>\n[IMG: 未生成的图片]\n<p>结尾</p>'
    result = run_gate(html, fallback_image_url="")
    assert not result.ok
    assert "占位符残留" in result.issues
    assert "[IMG:" not in result.fixed_html


def test_gate_removes_raw_video_tag():
    html = '<p>正文</p><video src="x.mp4"></video><p>结尾</p>'
    result = run_gate(html)
    assert not result.ok
    assert "<video" not in result.fixed_html
    assert "视频" in result.fixed_html  # 降级为说明卡片


def test_gate_strips_javascript():
    html = '<p onclick="alert(1)">正文</p><a href="javascript:void(0)">x</a>'
    result = run_gate(html)
    assert not result.ok
    assert "javascript:" not in result.fixed_html
    assert "onclick" not in result.fixed_html


def test_gate_img_without_src_removed():
    html = '<img class="broken"/>正文'
    result = run_gate(html)
    assert not result.ok
    assert "<img" not in result.fixed_html


def test_gate_uses_fallback_image_for_placeholders():
    html = '正文[IMG: 描述]结尾'
    result = run_gate(html, fallback_image_url="https://pexels/x.jpg")
    assert "https://pexels/x.jpg" in result.fixed_html


def test_clean_html_passes_gate():
    html = '<p>正常内容</p><img src="/media/images/a.png" style="max-width:100%"/>'
    result = run_gate(html)
    assert result.ok
    assert result.issues == []


def test_apply_lessons_incremental_dedup(tmp_path):
    store = SkillStore(base_dir=tmp_path / "skills")
    skill = store.load_default()
    result = run_gate('<video src="x"></video>')
    changes1 = apply_lessons(skill, result)
    assert len(changes1) >= 1
    v1 = skill.version
    # 第二次同一 lesson 不重复追加
    changes2 = apply_lessons(skill, result)
    assert changes2 == []
