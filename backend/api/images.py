"""
图片搜索 API 路由
"""
from fastapi import APIRouter
from pydantic import BaseModel
from service.images import search_images

router = APIRouter()


class ImageSearchRequest(BaseModel):
    query: str
    count: int = 12


@router.post("/search")
async def image_search(req: ImageSearchRequest):
    return search_images(req.query, req.count)
