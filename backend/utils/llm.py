"""
LLM 通用工具 - 所有 LLM 调用统一走这里
- strip_markdown_code_block: 去 ``` 包裹（Go 版 Bug 38 教训）
- extract_json: 提取 JSON 对象
- llm_chat: 超时/重试/可读错误包装
"""
import json
import re
from typing import List, Optional

from providers import get_llm, ChatMessage


def strip_markdown_code_block(s: str) -> str:
    """去掉 ```json {...} ``` 包裹，返回纯内容"""
    s = s.strip()
    if s.startswith("```"):
        if idx := s.find("\n"):
            s = s[idx + 1:]
        if idx := s.rfind("```"):
            s = s[:idx]
    return s.strip()


def extract_json(text: str) -> Optional[dict]:
    """从 LLM 输出中提取 JSON 对象（容忍 ``` 包裹和前后废话）"""
    cleaned = strip_markdown_code_block(text)
    # 直接解析
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    # 提取首 { 到末 }
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start >= 0 and end > start:
        try:
            return json.loads(cleaned[start:end + 1])
        except json.JSONDecodeError:
            return None
    return None


def llm_chat(messages: List[dict], model: str = None, timeout: int = 120, **kwargs) -> str:
    """统一 LLM 调用：超时/网络重试一次/错误转可读中文"""
    reg = get_llm()
    msgs = [ChatMessage(role=m["role"], content=m["content"]) for m in messages]
    try:
        resp = reg.chat(msgs, model=model, timeout=timeout, **kwargs)
        return resp.content or ""
    except (ValueError, RuntimeError, TimeoutError) as e:
        raise
    except Exception as e:
        raise RuntimeError(f"模型调用失败: {e}")
