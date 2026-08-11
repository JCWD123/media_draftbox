"""
视频生成 Provider
- ARKSeedanceProvider: 火山方舟 Seedance（异步任务 + 轮询，端点已验证）
扩展位: Kling / Veo / Sora —— 实现 VideoProvider 抽象即可接入
"""
import time
import requests
from abc import ABC, abstractmethod
from typing import Dict


class VideoProvider(ABC):
    """视频生成抽象"""

    name = ""
    base_url = ""

    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.api_key = self.config.get("api_key", "")
        self.model = self.config.get("model", "")
        self.base_url = self.config.get("base_url", self.base_url)

    @abstractmethod
    def generate(self, prompt: str, duration: int = 5) -> Dict:
        """生成视频（阻塞直至完成），返回 {"task_id":..., "video_url":..., "cover_url":...}"""
        pass


class ARKSeedanceProvider(VideoProvider):
    """火山方舟 Seedance - 异步任务模式（POST /contents/generations/tasks）"""

    name = "ark"
    base_url = "https://ark.cn-beijing.volces.com/api/v3"
    poll_interval = 5
    max_wait = 300  # 5 分钟上限

    def __init__(self, config: Dict = None):
        super().__init__(config)
        if not self.model:
            self.model = "doubao-seedance-1-0-pro-250528"

    def _session(self):
        s = requests.Session()
        s.trust_env = False  # 国内直连，绕开 Clash 代理
        return s

    def create_task(self, prompt: str, duration: int = 5) -> str:
        """创建生成任务，返回 task id"""
        if not self.api_key:
            raise ValueError("缺少 ARK API Key，请运行 draftbox config 配置 video.api_key")
        url = f"{self.base_url.rstrip('/')}/contents/generations/tasks"
        payload = {
            "model": self.model,
            # content 为必填参数（缺则 400 MissingParameter，已实测）
            "content": [{"type": "text", "text": prompt}],
            "duration": duration,
        }
        try:
            resp = self._session().post(
                url,
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json=payload,
                timeout=30,
            )
        except requests.RequestException as e:
            raise RuntimeError(f"视频任务创建失败: {e}")
        if resp.status_code != 200:
            raise RuntimeError(f"视频任务创建错误 {resp.status_code}: {resp.text[:300]}")
        return resp.json()["id"]

    def get_task(self, task_id: str) -> Dict:
        url = f"{self.base_url.rstrip('/')}/contents/generations/tasks/{task_id}"
        try:
            resp = self._session().get(
                url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=30,
            )
        except requests.RequestException as e:
            raise RuntimeError(f"视频任务查询失败: {e}")
        if resp.status_code != 200:
            raise RuntimeError(f"视频任务查询错误 {resp.status_code}: {resp.text[:300]}")
        return resp.json()

    def generate(self, prompt: str, duration: int = 5) -> Dict:
        """阻塞式生成（供后台任务线程调用）"""
        task_id = self.create_task(prompt, duration)
        waited = 0
        while waited < self.max_wait:
            time.sleep(self.poll_interval)
            waited += self.poll_interval
            task = self.get_task(task_id)
            status = task.get("status", "")
            if status == "succeeded":
                content = task.get("content") or {}
                video_url = ""
                cover_url = ""
                if isinstance(content, dict):
                    video_url = content.get("video_url") or content.get("url") or ""
                    cover_url = content.get("cover_url") or content.get("poster_url") or ""
                if not video_url:
                    raise RuntimeError(f"视频任务成功但缺少 video_url: {str(task)[:300]}")
                return {"task_id": task_id, "video_url": video_url, "cover_url": cover_url}
            if status in ("failed", "cancelled"):
                raise RuntimeError(f"视频生成失败（{status}）: {str(task)[:300]}")
        raise TimeoutError(f"视频生成超时（{self.max_wait}s），任务 {task_id} 仍在处理")
