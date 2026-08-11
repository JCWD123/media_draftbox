"""
垂直度测试 - 领域建模 / 漂移检测（LLM mock）
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest

from skill_core.vertical import build_domain, check_vertical
from skill_core.store import SkillStore


def test_build_domain_parses_llm_json(monkeypatch):
    monkeypatch.setattr("skill_core.vertical.llm_chat",
                        lambda messages, **kw: '{"domain": "科技AI", "tags": ["AI", "大模型"]}')
    domain = build_domain(None, ["AI 趋势", "大模型应用", "GPT 新功能"])
    assert domain == {"domain": "科技AI", "tags": ["AI", "大模型"]}


def test_build_domain_strips_code_block(monkeypatch):
    monkeypatch.setattr("skill_core.vertical.llm_chat",
                        lambda messages, **kw: '```json\n{"domain": "财经", "tags": ["股市"]}\n```')
    domain = build_domain(None, ["股市分析"])
    assert domain["domain"] == "财经"


def test_build_domain_empty_titles_returns_none():
    assert build_domain(None, []) is None


def test_check_vertical_no_domain_no_drift(tmp_path):
    store = SkillStore(base_dir=tmp_path / "skills")
    skill = store.load_default()  # 无 vertical 段
    result = check_vertical(["AI"], skill)
    assert not result.drifted


def test_check_vertical_drift_detected(monkeypatch, tmp_path):
    monkeypatch.setattr("skill_core.vertical.llm_chat",
                        lambda messages, **kw: '{"drifted": true, "reason": "标签偏离科技AI领域", "suggestion": "强化技术细节"}')
    store = SkillStore(base_dir=tmp_path / "skills")
    skill = store.load_default()
    skill.meta["vertical"] = {"domain": "科技AI", "tags": ["AI", "大模型"]}
    result = check_vertical(["娱乐", "明星"], skill)
    assert result.drifted
    assert "技术细节" in result.suggestion


def test_check_vertical_aligned(monkeypatch, tmp_path):
    monkeypatch.setattr("skill_core.vertical.llm_chat",
                        lambda messages, **kw: '{"drifted": false, "reason": "一致"}')
    store = SkillStore(base_dir=tmp_path / "skills")
    skill = store.load_default()
    skill.meta["vertical"] = {"domain": "科技AI", "tags": ["AI"]}
    result = check_vertical(["AI", "大模型"], skill)
    assert not result.drifted
