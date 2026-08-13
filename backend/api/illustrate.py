"""
文章配图 API 路由
"""
from fastapi import APIRouter
from model.schemas import IllustrateRequest
from service.illustrate import illustrate

router = APIRouter()


@router.post("")
async def illustrate_article(req: IllustrateRequest):
    return illustrate(req.html, req.material_md)
