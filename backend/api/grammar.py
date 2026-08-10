"""
语法检查 API 路由
"""
from fastapi import APIRouter
from pydantic import BaseModel
from service.grammar import check_grammar

router = APIRouter()


class GrammarCheckRequest(BaseModel):
    text: str
    language: str = "zh"


@router.post("/check")
async def grammar_check(req: GrammarCheckRequest):
    return check_grammar(req.text, req.language)
