"""
图片生成 Provider
- ARKSeedreamProvider: 火山方舟 Seedream（默认，国内直连，格式已验证）
- OpenAIImageProvider: OpenAI gpt-image-2（可选，国内需代理）
"""
import base64
import requests
from abc import ABC, abstractmethod
from typing import Dict


class ImageProvider(ABC):
    """图片生成抽象"""

    name = ""
    base_url = ""

    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.api_key = self.config.get("api_key", "")
        self.model = self.config.get("model", "")
        self.base_url = self.config.get("base_url", self.base_url)

    @abstractmethod
    def generate(self, prompt: str, size: str = "1920x1080") -> bytes:
        """生成图片，返回图片二进制"""
        pass


class ARKSeedreamProvider(ImageProvider):
    """火山方舟 Seedream（已验证格式，见 seedream-ark-image-api skill）"""

    name = "ark"
    base_url = "https://ark.cn-beijing.volces.com/api/v3"

    def __init__(self, config: Dict = None):
        super().__init__(config)
        if not self.model:
            self.model = "doubao-seedream-4-0-250828"

    def generate(self, prompt: str, size: str = "1920x1080") -> bytes:
        if not self.api_key:
            raise ValueError("缺少 ARK API Key，请运行 draftbox config 配置 image.api_key")

        url = f"{self.base_url.rstrip('/')}/images/generations"
        payload = {
            "model": self.model,
            "prompt": prompt,
            # 🔴 横版必须显式写 宽x高（写 "2K" 会得到竖版）
            "size": size,
            "response_format": "url",
            "watermark": False,
            # 不要传 output_format 参数（400 坑）
        }
        s = requests.Session()
        s.trust_env = False  # 国内直连，绕开 Clash 代理

        try:
            resp = s.post(
                url,
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json=payload,
                timeout=180,
            )
        except requests.RequestException as e:
            raise RuntimeError(f"图片生成请求失败: {e}")

        if resp.status_code != 200:
            raise RuntimeError(f"图片生成错误 {resp.status_code}: {resp.text[:300]}")

        data = resp.json()
        try:
            img_url = data["data"][0]["url"]
        except (KeyError, IndexError, TypeError):
            raise RuntimeError(f"图片生成响应异常: {resp.text[:300]}")

        # TOS 签名 URL 1 天过期，立即下载
        try:
            img_resp = s.get(img_url, timeout=60)
        except requests.RequestException as e:
            raise RuntimeError(f"图片下载失败: {e}")
        if img_resp.status_code != 200:
            raise RuntimeError(f"图片下载失败 {img_resp.status_code}")
        return img_resp.content


class OpenAIImageProvider(ImageProvider):
    """OpenAI gpt-image-2（国内需代理）"""

    name = "openai"
    base_url = "https://api.openai.com/v1"

    def __init__(self, config: Dict = None):
        super().__init__(config)
        if not self.model:
            self.model = "gpt-image-2"

    def generate(self, prompt: str, size: str = "1920x1080") -> bytes:
        if not self.api_key:
            raise ValueError("缺少 OpenAI API Key，请配置 image.api_key")

        url = f"{self.base_url.rstrip('/')}/images/generations"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "size": size,
            "n": 1,
            "response_format": "b64_json",
        }
        s = requests.Session()
        s.trust_env = True  # 走环境代理（国内访问 openai 需要）

        try:
            resp = s.post(
                url,
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json=payload,
                timeout=180,
            )
        except requests.RequestException as e:
            raise RuntimeError(f"图片生成请求失败: {e}")

        if resp.status_code != 200:
            raise RuntimeError(f"图片生成错误 {resp.status_code}: {resp.text[:300]}")

        data = resp.json()
        try:
            b64 = data["data"][0]["b64_json"]
        except (KeyError, IndexError, TypeError):
            raise RuntimeError(f"图片生成响应异常: {resp.text[:300]}")
        return base64.b64decode(b64)
