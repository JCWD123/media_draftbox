"""
转换 API 路由
"""
from fastapi import APIRouter
from model.schemas import ConvertRequest
from service.convert import convert_markdown, get_themes

router = APIRouter()


@router.post("/convert")
async def convert(req: ConvertRequest):
    return convert_markdown(req.markdown, req.theme)


@router.get("/themes")
async def themes():
    return get_themes()
