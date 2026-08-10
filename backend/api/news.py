"""
新闻 API 路由
"""
from fastapi import APIRouter
from model.schemas import NewsRequest
from service.news import get_categories, get_news_list

router = APIRouter()


@router.get("/categories")
async def categories():
    return get_categories()


@router.post("/list")
async def news_list(req: NewsRequest):
    return get_news_list(req.category, req.page, req.page_size)
