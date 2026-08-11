"""
SkillStore - SKILL.md 读写 / 版本管理 / 进化日志 / 生成记录

Skill 文件结构（与 Hermes SKILL.md 兼容）:
~/.draftbox/skills/<name>/
├── SKILL.md              # YAML frontmatter + Markdown 正文
├── evolution.jsonl       # 进化日志（append-only，无感自动写入）
└── generations.jsonl     # 生成记录（含媒体清单）
"""
import json
import re
import tempfile
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import yaml

# 默认 Skill 存储根目录
DEFAULT_BASE_DIR = Path.home() / ".draftbox" / "skills"

# 内置默认写作规范（无用户 skill 时的兜底模板，首次使用时落盘）
DEFAULT_SKILL_TEXT = """---
name: wechat-writing
version: 1
use_count: 0
adopt_rate: 1.0
created: 2026-08-10
updated: 2026-08-10
---

# 公众号文章写作规范（默认模板，随使用自动进化）

## style
### 开头
- ✅ 用一个具体场景/故事开头
- ❌ 不要用"最近XXX火了"

### 标题
- ✅ 数字 + 悬念（"3个方法..."）
- ❌ 标题党，与实际内容不符

### 段落
- ✅ 短段落为主，单段不超过 4 行
- ✅ 段落间用空行分隔

### 语气
- ✅ 专业但不生硬，口语化表达
- ❌ 空洞的形容词堆砌

## structure
- 开头钩子 → 正文 2-3 小节 → 金句收尾

## media
### 图片
- ✅ 每 2-3 段插入一张配图，与段落内容强相关
- ✅ 配图描述含场景/构图/风格，利于生成模型出图
- ❌ 图片不能出现在标题后第一段（先文字后图）
### 视频
- ✅ 全文最多 1-2 个视频，插在关键场景处
- ✅ 视频描述 5-10 秒动态场景，适合文章叙事
- ❌ 视频不放开头（先建立阅读节奏）

## anti_patterns
- ❌ "XXX为何霸榜热搜"
- ❌ 泛泛而谈，没有具体案例

## positive_examples

## formatting
- 小标题用 ##，列表用 -，图片放段间
- 媒体占位符 [IMG: 描述] / [VID: 描述] 只能出现在段落之间
"""


@dataclass
class Skill:
    """一个写作 Skill"""

    name: str
    raw_text: str = ""                    # SKILL.md 完整文本（frontmatter + 正文）
    meta: Dict = field(default_factory=dict)  # frontmatter 解析结果
    path: Optional[Path] = None

    @property
    def version(self) -> int:
        return int(self.meta.get("version", 1))

    @property
    def body(self) -> str:
        """frontmatter 之外的正文"""
        parts = self.raw_text.split("---", 2)
        if len(parts) >= 3:
            return parts[2].lstrip("\n")
        return self.raw_text


class SkillStore:
    """Skill 存储与版本管理"""

    def __init__(self, base_dir: Path = None):
        self.base_dir = Path(base_dir) if base_dir else DEFAULT_BASE_DIR
        self.base_dir.mkdir(parents=True, exist_ok=True)

    # ---------------- 读写 ----------------

    def load(self, name: str) -> Optional[Skill]:
        """加载 Skill；不存在且是默认名时自动落盘默认模板"""
        skill_dir = self._skill_dir(name)
        md = skill_dir / "SKILL.md"
        if not md.exists():
            if name == "wechat-writing":
                self._write_skill(skill_dir, DEFAULT_SKILL_TEXT)
                return self.load(name)
            return None
        raw = md.read_text(encoding="utf-8")
        meta = self._parse_frontmatter(raw)
        return Skill(name=name, raw_text=raw, meta=meta, path=skill_dir)

    def load_default(self) -> Skill:
        return self.load("wechat-writing")

    def save(self, skill: Skill):
        """原子写（tmp + rename，防断电损坏）"""
        skill_dir = self._skill_dir(skill.name)
        skill_dir.mkdir(parents=True, exist_ok=True)
        self._write_skill(skill_dir, skill.raw_text)

    def _write_skill(self, skill_dir: Path, text: str):
        skill_dir.mkdir(parents=True, exist_ok=True)
        target = skill_dir / "SKILL.md"
        fd, tmp_path = tempfile.mkstemp(dir=str(skill_dir), suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(text)
            os.replace(tmp_path, str(target))
        except Exception:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise

    def list_skills(self) -> List[str]:
        return sorted(d.name for d in self.base_dir.iterdir() if (d / "SKILL.md").exists())

    # ---------------- 版本与元数据 ----------------

    def bump_version(self, skill: Skill) -> int:
        """version+1 并更新 updated 时间戳，写回磁盘"""
        skill.meta["version"] = int(skill.meta.get("version", 1)) + 1
        skill.meta["updated"] = datetime.now().strftime("%Y-%m-%d")
        skill.raw_text = self._render_frontmatter(skill.meta, skill.body)
        self.save(skill)
        return skill.meta["version"]

    def update_meta(self, skill: Skill, **kv):
        """更新 frontmatter 字段（如 use_count/adopt_rate/vertical）并写回"""
        skill.meta.update(kv)
        skill.raw_text = self._render_frontmatter(skill.meta, skill.body)
        self.save(skill)

    # ---------------- 进化日志 ----------------

    def append_evolution(self, skill_name: str, entry: Dict):
        entry.setdefault("ts", datetime.now().strftime("%Y-%m-%dT%H:%M:%S"))
        with open(self._skill_dir(skill_name) / "evolution.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def load_evolution(self, skill_name: str) -> List[Dict]:
        path = self._skill_dir(skill_name) / "evolution.jsonl"
        if not path.exists():
            return []
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

    # ---------------- 生成记录 ----------------

    def save_generation(self, skill_name: str, gen: Dict):
        gen.setdefault("ts", datetime.now().strftime("%Y-%m-%dT%H:%M:%S"))
        with open(self._skill_dir(skill_name) / "generations.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(gen, ensure_ascii=False) + "\n")

    def list_generations(self, skill_name: str, limit: int = 50) -> List[Dict]:
        path = self._skill_dir(skill_name) / "generations.jsonl"
        if not path.exists():
            return []
        lines = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
        return lines[-limit:][::-1]

    # ---------------- 内部工具 ----------------

    def _skill_dir(self, name: str) -> Path:
        # 名称安全校验
        safe = re.sub(r"[^a-zA-Z0-9_-]", "", name) or "default"
        return self.base_dir / safe

    @staticmethod
    def _parse_frontmatter(raw: str) -> Dict:
        """解析 --- 包裹的 YAML frontmatter"""
        m = re.match(r"^---\s*\n(.*?)\n---\s*\n", raw, re.DOTALL)
        if not m:
            return {}
        try:
            meta = yaml.safe_load(m.group(1)) or {}
            return meta if isinstance(meta, dict) else {}
        except yaml.YAMLError:
            return {}

    @staticmethod
    def _render_frontmatter(meta: Dict, body: str) -> str:
        front = yaml.safe_dump(meta, allow_unicode=True, default_flow_style=False, sort_keys=False).strip()
        return f"---\n{front}\n---\n\n{body.lstrip(chr(10))}"
