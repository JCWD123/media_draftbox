"""
新闻 API 路由
"""
from fastapi import APIRouter
from model.schemas import NewsRequest, NewsSearchRequest, NewsSummarizeRequest
from service.news import get_categories, get_news_list
from service.summarize import summarize
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
    """自定义新闻搜索（ddgs实时搜索，付费Jina时优先，结果可勾选为写作素材）"""
    return search_news(req.query, req.limit)


@router.post("/summarize")
async def news_summarize(req: NewsSummarizeRequest):
    """新闻 AI 摘要（读者不点开原文即可了解大致内容）"""
    return summarize(req.title, req.summary, req.link)
