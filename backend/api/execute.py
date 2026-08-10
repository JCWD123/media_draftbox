"""
代码执行 API 路由
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
from tools.code_execution import executor

router = APIRouter()


class ExecuteScriptRequest(BaseModel):
    script_path: str
    args: List[str] = []
    timeout: int = 30


class ExecuteCodeRequest(BaseModel):
    code: str
    timeout: int = 30


class ExecuteSkillRequest(BaseModel):
    skill_name: str
    action: str = "run"
    args: List[str] = []


@router.post("/execute/script")
async def execute_script(req: ExecuteScriptRequest):
    """执行 Python 脚本"""
    result = executor.execute_script(req.script_path, req.args, timeout=req.timeout)
    return {
        "success": result.success,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "returncode": result.returncode,
        "duration": result.duration,
        "error": result.error,
    }


@router.post("/execute/code")
async def execute_code(req: ExecuteCodeRequest):
    """执行 Python 代码"""
    result = executor.execute_code(req.code, timeout=req.timeout)
    return {
        "success": result.success,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "returncode": result.returncode,
        "duration": result.duration,
        "error": result.error,
    }


@router.post("/execute/skill")
async def execute_skill(req: ExecuteSkillRequest):
    """执行 Skill"""
    result = executor.execute_skill(req.skill_name, req.action, req.args)
    return {
        "success": result.success,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "returncode": result.returncode,
        "duration": result.duration,
        "error": result.error,
    }


@router.get("/skills")
async def list_skills():
    """列出所有 Skills"""
    return {"skills": executor.list_skills()}
