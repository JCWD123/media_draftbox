"""
LLM 聊天 Provider - OpenAI 兼容格式
支持 MiMo / DeepSeek / OpenAI（三选一，由 config 的 model.provider 决定）
"""
import requests
from typing import Dict, List

from providers import Provider, ChatMessage, ChatResponse


class OpenAIStyleProvider(Provider):
    """OpenAI 兼容聊天 Provider 基类"""

    name = "openai-style"
    base_url = "https://api.openai.com/v1"

    def __init__(self, config: Dict = None):
        super().__init__(config)
        self.trust_env = True  # 默认走环境代理；国内直连 API 的子类覆盖为 False

    def _session(self):
        s = requests.Session()
        s.trust_env = self.trust_env
        return s

    def chat(self, messages: List[ChatMessage], model: str = None, **kwargs) -> ChatResponse:
        model = model or self.config.get("model", "")
        if not model:
            raise ValueError("未配置模型，请先运行 draftbox model 配置")
        if not self.api_key:
            raise ValueError("缺少 API Key，请先运行 draftbox model 配置模型")

        url = f"{self.base_url.rstrip('/')}/chat/completions"
        payload = {
            "model": model,
            "messages": [self._fmt(m) for m in messages],
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 4096),
        }
        timeout = kwargs.get("timeout", 120)
        try:
            resp = self._session().post(
                url,
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json=payload,
                timeout=timeout,
            )
        except requests.Timeout:
            raise TimeoutError(f"模型响应超时（{timeout}s），请重试")
        except requests.RequestException as e:
            raise RuntimeError(f"模型请求失败: {e}")

        if resp.status_code != 200:
            raise RuntimeError(f"模型 API 错误 {resp.status_code}: {resp.text[:300]}")

        data = resp.json()
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as e:
            raise RuntimeError(f"模型响应格式异常: {e}")

        return ChatResponse(
            content=content if isinstance(content, str) else str(content),
            model=data.get("model", model),
            usage=data.get("usage"),
            finish_reason=(data.get("choices") or [{}])[0].get("finish_reason", ""),
        )

    @staticmethod
    def _fmt(msg):
        if isinstance(msg, ChatMessage):
            return {"role": msg.role, "content": msg.content}
        return {"role": msg.get("role", "user"), "content": msg.get("content", "")}

    def list_models(self):
        return []


class MimoProvider(OpenAIStyleProvider):
    """小米 MiMo v2.5（国内直连）"""

    name = "mimo"
    base_url = "https://token-plan-cn.xiaomimimo.com/v1"
    trust_env = False


class DeepSeekProvider(OpenAIStyleProvider):
    """DeepSeek（国内直连）"""

    name = "deepseek"
    base_url = "https://api.deepseek.com/v1"
    trust_env = False


class OpenAIChatProvider(OpenAIStyleProvider):
    """OpenAI（国内需代理）"""

    name = "openai"
    base_url = "https://api.openai.com/v1"
    trust_env = True
