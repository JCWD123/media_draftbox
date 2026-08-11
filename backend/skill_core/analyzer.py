"""
SkillAnalyzer - 参考文章学习管线（8 维度风格提取 + 增量追加）

学习流程: 参考文章 → LLM 8 维度分析 → 增量追加（去重）→ version+1
"""
from typing import Dict, List, Optional

from utils.llm import llm_chat, extract_json


ANALYZE_PROMPT = """你是一位公众号写作教练。请分析下面这篇文章的写作风格，提取可复用的技巧。
输出 JSON，格式严格如下：
{"style": {"标题模式": "...", "开头风格": "...", "段落长度": "...", "列表风格": "...", "引用风格": "...", "语气风格": "...", "数据使用": "...", "结尾模式": "..."}, "techniques": ["具体可操作的技巧，3-8条"], "anti_patterns": ["作者明显在避免的写法，0-5条"]}
只输出 JSON，不要 markdown 代码块。
---文章开始---
{content}
---文章结束---"""


def analyze_article(title: str, content: str) -> Optional[Dict]:
    """LLM 分析文章风格，返回 {"style": {...}, "techniques": [...], "anti_patterns": [...]}"""
    text = f"标题: {title}\n\n{content}" if title else content
    if len(text) > 20000:
        text = text[:20000]  # 截断保护
    try:
        # ⚠️ 用 replace 而非 str.format：prompt 内含 JSON 花括号会被 format 误解析
        prompt = ANALYZE_PROMPT.replace("{content}", text)
        raw = llm_chat([{"role": "user", "content": prompt}])
        data = extract_json(raw)
        if data is None or not isinstance(data, dict):
            return None
        return data
    except Exception:
        return None


def apply_analysis(skill, analysis: Dict) -> List[str]:
    """
    增量追加分析结果到 skill（核心：去重检查 → 不存在才添加）
    返回实际新增的变更列表；空列表 = 无新内容（不 bump version）
    """
    changes: List[str] = []
    yaml_text = skill.raw_text

    # techniques → 追加到 style 相关位置（正文末尾 techniques 章节不存在则建）
    for tech in analysis.get("techniques", []) or []:
        tech = str(tech).strip()
        if tech and tech not in yaml_text:
            yaml_text += f"\n- {tech}"
            changes.append(tech)

    # anti_patterns → 追加
    for anti in analysis.get("anti_patterns", []) or []:
        anti = str(anti).strip()
        if anti and anti not in yaml_text:
            yaml_text += f"\n- ❌ {anti}"
            changes.append(f"anti: {anti}")

    # style 8 维度 → 更新对应维度（同维度覆盖旧值；值相同则跳过去重）
    style = analysis.get("style") or {}
    if isinstance(style, dict):
        for dim, val in style.items():
            val = str(val or "").strip()
            if not val:
                continue
            dim = str(dim).strip()
            if f"- {val}" in yaml_text:  # 该值已存在 → 去重跳过
                continue
            yaml_text = _upsert_style_dimension(yaml_text, dim, val)
            changes.append(f"style.{dim}: {val}")

    skill.raw_text = yaml_text
    return changes


def _upsert_style_dimension(yaml_text: str, dim: str, val: str) -> str:
    """在 ## style 章节下更新某个维度（存在则替换旧值，不存在则追加）"""
    marker = f"### {dim}"
    if marker in yaml_text:
        # 替换该维度标题下的第一行内容
        lines = yaml_text.splitlines()
        out = []
        in_dim = False
        replaced = False
        for line in lines:
            if line.strip() == marker:
                in_dim = True
                out.append(line)
                continue
            if in_dim:
                if line.strip().startswith("### ") or line.strip().startswith("## "):
                    in_dim = False
                elif line.strip() and not replaced:
                    out.append(f"- {val}")
                    replaced = True
                    continue
            out.append(line)
        if not replaced:
            # 维度存在但无内容行 → 追加
            out.append(f"- {val}")
        return "\n".join(out)
    # 维度不存在 → 在 style 章节末尾追加
    return yaml_text + f"\n### {dim}\n- {val}"


def learn_from_article(store, skill_name: str, title: str, content: str, source: str = "") -> Dict:
    """
    完整学习流程：分析 → 增量追加 → 有变化则 version+1 + 写进化日志
    返回 {"success", "learned", "changes", "skill_version"}（learned=False 表示无新内容）
    """
    skill = store.load(skill_name) or store.load_default()
    analysis = analyze_article(title, content)
    if analysis is None:
        return {"success": False, "error": "文章分析失败（模型未配置或返回异常）"}

    changes = apply_analysis(skill, analysis)
    if not changes:
        return {"success": True, "learned": False, "message": "无新内容可学习", "skill_version": skill.version}

    store.bump_version(skill)
    store.append_evolution(skill.name, {"type": "learn", "source": source or "manual", "changes": changes[:10]})
    return {"success": True, "learned": True, "changes": changes[:10], "skill_version": skill.version}
