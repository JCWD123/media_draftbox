"""
学习管线测试 - 增量追加 / 去重 / 幂等
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest

from skill_core.analyzer import analyze_article, apply_analysis, learn_from_article
from skill_core.store import SkillStore


def test_analyze_article_parses_json(monkeypatch):
    monkeypatch.setattr("skill_core.analyzer.llm_chat",
                        lambda messages, **kw: '{"style": {"开头风格": "场景开头"}, "techniques": ["用具体场景开头", "数据佐证"], "anti_patterns": ["不要标题党"]}')
    analysis = analyze_article("标题", "正文内容")
    assert analysis["techniques"] == ["用具体场景开头", "数据佐证"]
    assert analysis["anti_patterns"] == ["不要标题党"]


def test_analyze_article_strips_code_block(monkeypatch):
    monkeypatch.setattr("skill_core.analyzer.llm_chat",
                        lambda messages, **kw: '```json\n{"techniques": ["技巧A"]}\n```')
    analysis = analyze_article("t", "c")
    assert analysis["techniques"] == ["技巧A"]


def test_apply_analysis_incremental_no_duplicate(tmp_path):
    store = SkillStore(base_dir=tmp_path / "skills")
    skill = store.load_default()
    analysis = {"techniques": ["用具体场景开头", "数据佐证"], "anti_patterns": ["不要标题党"], "style": {"开头风格": "场景开头"}}
    changes1 = apply_analysis(skill, analysis)
    assert len(changes1) == 4  # 2 techniques + 1 anti + 1 style
    # 再应用相同分析 → 全部去重
    changes2 = apply_analysis(skill, analysis)
    assert changes2 == []


def test_learn_from_article_bumps_version_once(tmp_path, monkeypatch):
    monkeypatch.setattr("skill_core.analyzer.llm_chat",
                        lambda messages, **kw: '{"techniques": ["新技巧X"], "style": {"语气风格": "口语"}}')
    store = SkillStore(base_dir=tmp_path / "skills")
    r1 = learn_from_article(store, "wechat-writing", "t", "content")
    assert r1["learned"] is True
    v1 = r1["skill_version"]
    # 重复学习同一内容（LLM 返回相同技巧）→ 无新内容，版本不变
    r2 = learn_from_article(store, "wechat-writing", "t", "content")
    assert r2["learned"] is False
    assert r2["skill_version"] == v1


def test_learn_from_article_failure_no_version_change(tmp_path, monkeypatch):
    monkeypatch.setattr("skill_core.analyzer.llm_chat", lambda messages, **kw: "not json at all")
    store = SkillStore(base_dir=tmp_path / "skills")
    skill = store.load_default()
    v0 = skill.version
    r = learn_from_article(store, "wechat-writing", "t", "content")
    assert r["success"] is False
    assert store.load_default().version == v0


def test_evolution_log_written_on_learn(tmp_path, monkeypatch):
    monkeypatch.setattr("skill_core.analyzer.llm_chat",
                        lambda messages, **kw: '{"techniques": ["技巧Y"], "style": {}}')
    store = SkillStore(base_dir=tmp_path / "skills")
    learn_from_article(store, "wechat-writing", "t", "content", source="https://x.com/a")
    log = store.load_evolution("wechat-writing")
    assert any(e["type"] == "learn" and e["source"] == "https://x.com/a" for e in log)
