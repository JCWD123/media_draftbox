"""
AI 写作 API 路由
"""
from fastapi import APIRouter
from model.schemas import WriteRequest
from service.writing import generate_article, media_status

router = APIRouter()


@router.post("/write/generate")
async def write_generate(req: WriteRequest):
    """三模态生成（文字 + 图片 + 视频）"""
    return generate_article(req)


@router.get("/write/media-status")
async def write_media_status(draft_id: str):
    """视频后台任务状态（前端轮询）"""
    return media_status(draft_id)
