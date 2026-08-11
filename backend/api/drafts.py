"""
草稿管理 API 路由
"""
from fastapi import APIRouter, HTTPException
from model.schemas import DraftSaveRequest
from service.drafts import list_drafts, save_draft, get_draft, delete_draft

router = APIRouter()


@router.get("")
async def get_drafts():
    return list_drafts()


@router.post("")
async def save(req: DraftSaveRequest):
    return save_draft(req.title, req.content, req.html)


@router.get("/{filename}")
async def get(filename: str):
    result = get_draft(filename)
    if result is None:
        raise HTTPException(404, "草稿不存在")
    return result


@router.delete("/{filename}")
async def delete(filename: str):
    return delete_draft(filename)
