"""
SkillStore 测试 - 读写/原子写/版本/日志/生成记录
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest

from skill_core.store import SkillStore, Skill, DEFAULT_SKILL_TEXT


@pytest.fixture
def store(tmp_path):
    return SkillStore(base_dir=tmp_path / "skills")


def test_load_default_creates_skill_on_disk(store):
    skill = store.load_default()
    assert skill.name == "wechat-writing"
    assert skill.version == 1
    assert (store.base_dir / "wechat-writing" / "SKILL.md").exists()


def test_load_nonexistent_returns_none(store):
    assert store.load("no-such-skill") is None


def test_bump_version_persists(store):
    skill = store.load_default()
    v = store.bump_version(skill)
    assert v == 2
    reloaded = store.load_default()
    assert reloaded.version == 2
    assert "version: 2" in reloaded.raw_text


def test_append_and_load_evolution(store):
    skill = store.load_default()
    store.append_evolution(skill.name, {"version": 2, "type": "learn", "changes": ["a"]})
    store.append_evolution(skill.name, {"version": 3, "type": "gate", "lesson": "b"})
    log = store.load_evolution(skill.name)
    assert len(log) == 2
    assert log[0]["type"] == "learn"
    assert log[1]["lesson"] == "b"
    assert "ts" in log[0]


def test_save_generation_and_list(store):
    skill = store.load_default()
    store.save_generation(skill.name, {"draft_id": "gen_1", "title": "t"})
    store.save_generation(skill.name, {"draft_id": "gen_2", "title": "t2"})
    gens = store.list_generations(skill.name)
    assert len(gens) == 2
    assert gens[0]["draft_id"] == "gen_2"  # 最新在前


def test_update_meta_preserves_body(store):
    skill = store.load_default()
    original_body = skill.body
    store.update_meta(skill, use_count=5, adopt_rate=0.9)
    reloaded = store.load_default()
    assert reloaded.meta["use_count"] == 5
    assert reloaded.body == original_body  # 正文不被 frontmatter 重写破坏


def test_list_skills(store):
    store.load_default()
    assert store.list_skills() == ["wechat-writing"]


def test_unsafe_name_is_sanitized(store):
    skill = store.load("../../evil")
    assert skill is None  # 不存在的名字不会创建
    assert not (store.base_dir.parent / "evil").exists()
