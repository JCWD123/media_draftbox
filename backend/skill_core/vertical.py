"""
垂直度校准 - 内容垂直化 / 标签不混乱（无感自进化核心之二）
生成文章标签与账号垂直领域自动比对，偏离时记录并给出调整方向
"""
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from utils.llm import llm_chat, extract_json


@dataclass
class VerticalResult:
    """垂直度校验结果"""

    drifted: bool = False
    domain: str = ""
    note: str = ""
    suggestion: str = ""  # 调整方向建议
    tags: List[str] = field(default_factory=list)


def build_domain(skill, article_titles: List[str]) -> Optional[Dict]:
    """
    领域建模：从学习目标公众号的文章标题聚类出垂直领域
    返回 {"domain": "科技AI", "tags": [...]}，由调用方写入 skill.meta.vertical
    """
    if not article_titles:
        return None
    sample = "\n".join(f"- {t}" for t in article_titles[:30])
    prompt = (
        "以下是某个公众号的近期文章标题。请总结该账号的内容垂直领域。\n"
        f"{sample}\n\n"
        '只输出 JSON：{"domain": "领域名（2-8字）", "tags": ["3-8个该领域标签"]}'
    )
    try:
        raw = llm_chat([{"role": "user", "content": prompt}])
        data = extract_json(raw)
        if data and data.get("domain"):
            return {"domain": data["domain"], "tags": data.get("tags", [])}
    except Exception:
        pass
    return None


def check_vertical(tags: List[str], skill, domain: Optional[Dict] = None) -> VerticalResult:
    """
    标签与领域比对。领域缺失时直接返回不漂移（无信号不误判）。
    """
    domain = domain or (skill.meta.get("vertical") if skill else None)
    if not domain or not domain.get("domain"):
        return VerticalResult(domain=(domain or {}).get("domain", ""), tags=tags or [])

    if not tags:
        return VerticalResult(drifted=False, domain=domain["domain"], tags=[])

    result = VerticalResult(domain=domain["domain"], tags=tags)
    domain_tags = domain.get("tags", [])
    prompt = (
        "判断一组文章标签是否偏离某账号的内容垂直领域。\n"
        f"账号领域: {domain['domain']}（代表标签: {', '.join(domain_tags)}）\n"
        f"文章标签: {', '.join(tags)}\n\n"
        '只输出 JSON：{"drifted": true/false, "reason": "一句话原因", '
        '"suggestion": "若漂移，给一条调整方向建议（如：强化技术细节，弱化娱乐表述）"}'
    )
    try:
        raw = llm_chat([{"role": "user", "content": prompt}])
        data = extract_json(raw) or {}
        result.drifted = bool(data.get("drifted"))
        result.note = data.get("reason", "")
        result.suggestion = data.get("suggestion", "")
    except Exception:
        pass
    return result
