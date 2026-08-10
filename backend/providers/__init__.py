"""
模型提供商基类 - 参考 hermes-agent providers
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
import requests


@dataclass
class ModelInfo:
    """模型信息"""
    id: str
    name: str
    description: str = ""
    max_tokens: int = 4096
    supports_streaming: bool = True


@dataclass
class ChatMessage:
    """聊天消息"""
    role: str  # system, user, assistant
    content: str


@dataclass
class ChatResponse:
    """聊天响应"""
    content: str
    model: str = ""
    usage: Dict = None
    finish_reason: str = ""


class Provider(ABC):
    """模型提供商基类"""

    name: str = ""
    base_url: str = ""
    api_key: str = ""

    def __init__(self, config: Dict = None):
        self.config = config or {}
        if config:
            self.api_key = config.get("api_key", "")
            self.base_url = config.get("base_url", self.base_url)

    @abstractmethod
    def chat(self, messages: List[ChatMessage], model: str = None, **kwargs) -> ChatResponse:
        """聊天接口"""
        pass

    @abstractmethod
    def list_models(self) -> List[ModelInfo]:
        """列出可用模型"""
        pass

    def health_check(self) -> bool:
        """健康检查"""
        try:
            resp = requests.get(f"{self.base_url}/models", timeout=5)
            return resp.status_code == 200
        except:
            return False


class ProviderRegistry:
    """提供商注册表"""

    def __init__(self):
        self.providers: Dict[str, Provider] = {}
        self.current_provider: str = ""
        self.current_model: str = ""

    def register(self, provider: Provider):
        """注册提供商"""
        self.providers[provider.name] = provider

    def set_current(self, provider_name: str, model: str = None):
        """设置当前使用的提供商"""
        if provider_name in self.providers:
            self.current_provider = provider_name
            if model:
                self.current_model = model

    def get_current(self) -> Optional[Provider]:
        """获取当前提供商"""
        return self.providers.get(self.current_provider)

    def chat(self, messages: List[ChatMessage], **kwargs) -> ChatResponse:
        """使用当前提供商聊天"""
        provider = self.get_current()
        if not provider:
            raise ValueError("未设置模型提供商")
        return provider.chat(messages, model=self.current_model, **kwargs)

    def list_providers(self) -> List[Dict]:
        """列出所有提供商"""
        return [
            {"name": p.name, "current": p.name == self.current_provider}
            for p in self.providers.values()
        ]
