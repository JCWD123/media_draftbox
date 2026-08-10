"""
语法检查工具 - 参考 hermes-agent 工具系统
"""
from tools import Tool, ToolResult
import requests


class GrammarCheckTool(Tool):
    """语法检查工具"""

    name = "grammar_check"
    description = "语法检查（支持 20+ 语言）"
    parameters = {
        "text": {"type": "string", "description": "待检查文本", "required": True},
        "language": {"type": "string", "description": "语言代码", "default": "zh"},
    }

    def execute(self, text: str, language: str = "zh", **kwargs) -> ToolResult:
        try:
            url = "https://api.languagetool.org/v2/check"
            data = {"text": text, "language": language}
            response = requests.post(url, data=data, timeout=10)
            result = response.json()
            matches = result.get("matches", [])
            return ToolResult(
                success=True,
                data={
                    "matches": matches,
                    "total": len(matches),
                    "text": text,
                }
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))
