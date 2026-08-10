"""
插件系统 API 路由
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any
from plugins import PluginManager
from tools import ToolRegistry
from providers import ProviderRegistry

router = APIRouter()

# 全局实例
plugin_manager = PluginManager()
tool_registry = ToolRegistry()
provider_registry = ProviderRegistry()


class ToolExecuteRequest(BaseModel):
    tool_name: str
    params: Dict[str, Any] = {}


class ProviderSetRequest(BaseModel):
    provider_name: str
    model: str = None


@router.get("/plugins")
async def list_plugins():
    """列出所有插件"""
    return {"plugins": plugin_manager.list_plugins()}


@router.post("/plugins/{name}/enable")
async def enable_plugin(name: str):
    """启用插件"""
    plugin_manager.enable_plugin(name)
    return {"ok": True}


@router.post("/plugins/{name}/disable")
async def disable_plugin(name: str):
    """禁用插件"""
    plugin_manager.disable_plugin(name)
    return {"ok": True}


@router.get("/tools")
async def list_tools():
    """列出所有工具"""
    return {"tools": tool_registry.list_tools()}


@router.post("/tools/execute")
async def execute_tool(req: ToolExecuteRequest):
    """执行工具"""
    result = tool_registry.execute(req.tool_name, **req.params)
    return {"success": result.success, "data": result.data, "error": result.error}


@router.get("/providers")
async def list_providers():
    """列出所有提供商"""
    return {"providers": provider_registry.list_providers()}


@router.post("/providers/set")
async def set_provider(req: ProviderSetRequest):
    """设置当前提供商"""
    provider_registry.set_current(req.provider_name, req.model)
    return {"ok": True}
