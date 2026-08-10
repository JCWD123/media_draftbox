"""
图片搜索 API 路由
"""
from fastapi import APIRouter
from model.schemas import ImageSearchRequest
from service.images import search_images

router = APIRouter()


@router.post("/search")
async def image_search(req: ImageSearchRequest):
    return search_images(req.query, req.count)
