"""
草稿管理 API 路由
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from service.drafts import list_drafts, save_draft, get_draft, delete_draft

router = APIRouter()


class DraftSaveRequest(BaseModel):
    title: str
    content: str


@router.get("")
async def get_drafts():
    return list_drafts()


@router.post("")
async def save(req: DraftSaveRequest):
    return save_draft(req.title, req.content)


@router.get("/{filename}")
async def get(filename: str):
    result = get_draft(filename)
    if result is None:
        raise HTTPException(404, "草稿不存在")
    return result


@router.delete("/{filename}")
async def delete(filename: str):
    return delete_draft(filename)
