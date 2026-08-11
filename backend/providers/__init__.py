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
            raise ValueError("未设置模型提供商，请先运行 draftbox model 配置")
        # 调用方显式传 model 时优先，否则用当前配置的 model
        if "model" not in kwargs:
            kwargs["model"] = self.current_model
        return provider.chat(messages, **kwargs)

    def list_providers(self) -> List[Dict]:
        """列出所有提供商"""
        return [
            {"name": p.name, "current": p.name == self.current_provider}
            for p in self.providers.values()
        ]


# ---------------------------------------------------------------
# 三套 Provider 全局注册（LLM + 图片 + 视频）
# 由 main.py 启动时调用 init_registry()，service 层通过 get_* 获取
# ---------------------------------------------------------------

_llm: Optional[ProviderRegistry] = None
_image: Optional["ImageProvider"] = None  # noqa: F821
_video: Optional["VideoProvider"] = None  # noqa: F821


def init_registry(cfg: Dict = None):
    """初始化三套 Provider（配置优先用传入 dict，否则读 ~/.draftbox/config.yaml）"""
    global _llm, _image, _video

    if cfg is None:
        from utils.config import load_config
        cfg = load_config()

    from providers.chat import MimoProvider, DeepSeekProvider, OpenAIChatProvider
    from providers.image_gen import ARKSeedreamProvider, OpenAIImageProvider
    from providers.video_gen import ARKSeedanceProvider

    # --- LLM ---
    _llm = ProviderRegistry()
    model_cfg = cfg.get("model") or {}
    for p in (MimoProvider(model_cfg), DeepSeekProvider(model_cfg), OpenAIChatProvider(model_cfg)):
        _llm.register(p)
    if model_cfg.get("provider") in _llm.providers:
        _llm.set_current(model_cfg["provider"], model_cfg.get("model"))

    # --- 图片 ---
    img_cfg = cfg.get("image") or {}
    _image = OpenAIImageProvider(img_cfg) if img_cfg.get("provider") == "openai" else ARKSeedreamProvider(img_cfg)

    # --- 视频 ---
    vid_cfg = cfg.get("video") or {}
    _video = ARKSeedanceProvider(vid_cfg)


def get_llm() -> Optional[ProviderRegistry]:
    """获取 LLM 注册表（未初始化则自动初始化）"""
    global _llm
    if _llm is None:
        init_registry()
    return _llm


def get_image():
    """获取图片 Provider（未配置 key 时 generate 抛可读错误）"""
    global _image
    if _image is None:
        init_registry()
    return _image


def get_video():
    """获取视频 Provider（未配置 key 时 create_task 抛可读错误）"""
    global _video
    if _video is None:
        init_registry()
    return _video
