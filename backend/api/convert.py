"""
转换 API 路由
"""
from fastapi import APIRouter
from pydantic import BaseModel
from service.convert import convert_markdown

router = APIRouter()


class ConvertRequest(BaseModel):
    markdown: str
    theme: str = "professional-clean"


@router.post("/convert")
async def convert(req: ConvertRequest):
    return convert_markdown(req.markdown, req.theme)


@router.get("/themes")
async def themes():
    from service.convert import get_themes
    return get_themes()
