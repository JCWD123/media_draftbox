"""
Skill 内部 API（前端不展示 UI）
- current / targets / learn / evolution / generations
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import List, Optional

from skill_core.store import SkillStore
from skill_core.analyzer import learn_from_article
from service import skill_engine

router = APIRouter()


class LearnRequest(BaseModel):
    title: str = Field(default="", max_length=200)
    content: str = Field(..., min_length=50, max_length=100000, description="参考文章全文")
    source: str = Field(default="", max_length=500, description="来源（URL 或手动）")
    images: List[str] = Field(default=[], max_length=10)
    skill_name: str = Field(default="wechat-writing", max_length=50)


class TargetRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    url: str = Field(..., min_length=5, max_length=500)
    weight: int = Field(default=1, ge=1, le=10)


class FetchUrlRequest(BaseModel):
    url: str = Field(..., min_length=5, max_length=500)


@router.get("/skill/current")
async def skill_current(skill_name: str = "wechat-writing"):
    """当前 Skill（YAML + version + vertical）"""
    store = SkillStore()
    skill = store.load(skill_name) or store.load_default()
    return {
        "success": True,
        "name": skill.name,
        "version": skill.version,
        "use_count": skill.meta.get("use_count", 0),
        "vertical": skill.meta.get("vertical"),
        "yaml": skill.raw_text,
    }


@router.get("/skill/targets")
async def skill_targets():
    return {"success": True, "targets": skill_engine.load_targets()}


@router.post("/skill/targets")
async def skill_add_target(req: TargetRequest):
    return skill_engine.add_target(req.name, req.url, req.weight)


@router.post("/skill/learn")
async def skill_learn(req: LearnRequest):
    """参考文章提交 + 分析 + 增量进化（幂等：重复内容不重复进化）"""
    result = learn_from_article(SkillStore(), req.skill_name, req.title, req.content, source=req.source)
    return {"success": result["success"], **{k: v for k, v in result.items() if k != "success"}}


@router.post("/skill/fetch-url")
async def skill_fetch_url(req: FetchUrlRequest):
    """URL 抓取学习（微信反爬失败时提示手动粘贴降级）"""
    from service.wechat_fetcher import fetch_url
    article = fetch_url(req.url)
    if not article:
        return {"success": False, "error": "抓取失败（可能是微信反爬），请手动复制文章内容到「学习」接口"}
    result = learn_from_article(SkillStore(), "wechat-writing", article["title"], article["content"], source=req.url)
    return {"success": result["success"], "title": article["title"], **{k: v for k, v in result.items() if k != "success"}}


@router.get("/skill/evolution")
async def skill_evolution(skill_name: str = "wechat-writing", limit: int = 50):
    store = SkillStore()
    log = store.load_evolution(skill_name)[-limit:][::-1]
    return {"success": True, "evolution": log}


@router.get("/skill/generations")
async def skill_generations(skill_name: str = "wechat-writing", limit: int = 50):
    store = SkillStore()
    gens = store.list_generations(skill_name, limit=limit)
    return {"success": True, "generations": gens}
