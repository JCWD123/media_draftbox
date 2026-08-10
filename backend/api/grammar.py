"""
语法检查 API 路由
"""
from fastapi import APIRouter
from model.schemas import GrammarCheckRequest
from service.grammar import check_grammar

router = APIRouter()


@router.post("/check")
async def grammar_check(req: GrammarCheckRequest):
    return check_grammar(req.text, req.language)
