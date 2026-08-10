"""
新闻 API 路由
"""
from fastapi import APIRouter
from pydantic import BaseModel
from service.news import get_categories, get_news_list

router = APIRouter()


class NewsRequest(BaseModel):
    category: str = "TECH"
    page: int = 1
    page_size: int = 20


@router.get("/categories")
async def categories():
    return get_categories()


@router.post("/list")
async def news_list(req: NewsRequest):
    return get_news_list(req.category, req.page, req.page_size)
