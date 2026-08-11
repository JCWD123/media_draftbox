"""
新闻 API 路由
"""
from fastapi import APIRouter
from model.schemas import NewsRequest, NewsSearchRequest
from service.news import get_categories, get_news_list
from tools.custom_search import search_news

router = APIRouter()


@router.get("/categories")
async def categories():
    return get_categories()


@router.post("/list")
async def news_list(req: NewsRequest):
    return get_news_list(req.category, req.page, req.page_size)


@router.post("/search")
async def news_search(req: NewsSearchRequest):
    """自定义新闻搜索（ddgs 实时搜索，结果可勾选为写作素材）"""
    return search_news(req.query, req.limit)
