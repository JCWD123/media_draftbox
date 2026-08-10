"""
工具基类 - 参考 hermes-agent 工具系统
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
import json


@dataclass
class ToolResult:
    """工具执行结果"""
    success: bool
    data: Any = None
    error: str = ""
    metadata: Dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class Tool(ABC):
    """工具基类"""

    name: str = ""
    description: str = ""
    parameters: Dict = {}

    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """执行工具"""
        pass

    def validate_params(self, params: Dict) -> bool:
        """验证参数"""
        for key, schema in self.parameters.items():
            if schema.get("required", False) and key not in params:
                return False
        return True

    def get_schema(self) -> Dict:
        """获取工具 Schema（用于 LLM function calling）"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": self.parameters,
                "required": [k for k, v in self.parameters.items() if v.get("required", False)],
            },
        }


class ToolRegistry:
    """工具注册表"""

    def __init__(self):
        self.tools: Dict[str, Tool] = {}

    def register(self, tool: Tool):
        """注册工具"""
        self.tools[tool.name] = tool

    def get(self, name: str) -> Optional[Tool]:
        """获取工具"""
        return self.tools.get(name)

    def list_tools(self) -> List[Dict]:
        """列出所有工具"""
        return [tool.get_schema() for tool in self.tools.values()]

    def execute(self, name: str, **kwargs) -> ToolResult:
        """执行工具"""
        tool = self.tools.get(name)
        if not tool:
            return ToolResult(success=False, error=f"工具 {name} 不存在")

        if not tool.validate_params(kwargs):
            return ToolResult(success=False, error=f"工具 {name} 参数验证失败")

        try:
            return tool.execute(**kwargs)
        except Exception as e:
            return ToolResult(success=False, error=str(e))
