"""
Provider 测试 - 三套（LLM / 图片 / 视频）
LLM/图片/视频请求全部 mock，不真调 API
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest
import requests


# ---------------------------------------------------------------
# LLM Registry
# ---------------------------------------------------------------

def test_llm_registry_registers_three_providers():
    from providers import init_registry
    cfg = {"model": {"provider": "mimo", "model": "mimo-v2.5-pro", "api_key": "sk-test",
                     "base_url": "https://token-plan-cn.xiaomimimo.com/v1"}}
    init_registry(cfg)
    from providers import get_llm
    reg = get_llm()
    assert set(reg.providers.keys()) >= {"mimo", "deepseek", "openai"}
    assert reg.current_provider == "mimo"
    assert reg.current_model == "mimo-v2.5-pro"


def test_llm_without_model_config_raises_readable_error():
    from providers import init_registry, get_llm
    init_registry({"model": {}})
    with pytest.raises(ValueError) as e:
        get_llm().chat([{"role": "user", "content": "hi"}])
    assert "draftbox model" in str(e.value)


def test_llm_chat_calls_openai_compatible_endpoint(monkeypatch):
    from providers import init_registry, get_llm
    from providers import ChatMessage

    captured = {}

    class FakeResp:
        status_code = 200

        def json(self):
            return {"choices": [{"message": {"content": "你好"}, "finish_reason": "stop"}],
                    "model": "mimo-v2.5-pro", "usage": {}}

    def fake_post(self, url, headers=None, json=None, timeout=None):
        captured["url"] = url
        captured["payload"] = json
        return FakeResp()

    init_registry({"model": {"provider": "mimo", "model": "mimo-v2.5-pro", "api_key": "sk-test",
                             "base_url": "https://token-plan-cn.xiaomimimo.com/v1"}})
    monkeypatch.setattr(requests.Session, "post", fake_post)

    resp = get_llm().chat([ChatMessage(role="user", content="你好")])
    assert resp.content == "你好"
    assert "/chat/completions" in captured["url"]
    assert captured["payload"]["model"] == "mimo-v2.5-pro"
    assert captured["payload"]["messages"][0]["role"] == "user"


# ---------------------------------------------------------------
# 图片 Provider（Seedream 请求体构造）
# ---------------------------------------------------------------

def test_seedream_generate_builds_payload_and_downloads(monkeypatch):
    from providers.image_gen import ARKSeedreamProvider

    calls = []

    class FakeImgResp:
        status_code = 200
        content = b"\xff\xd8fake-image"

        def json(self):
            return {"data": [{"url": "https://tos.xxx/sig.png"}]}

    class FakeDownloadResp:
        status_code = 200
        content = b"\xff\xd8fake-image"

    def fake_post(self, url, headers=None, json=None, timeout=None):
        calls.append(("post", url, json))
        return FakeImgResp()

    def fake_get(self, url, timeout=None):
        calls.append(("get", url))
        return FakeDownloadResp()

    p = ARKSeedreamProvider({"api_key": "sk-ark", "base_url": "https://ark.cn-beijing.volces.com/api/v3"})
    monkeypatch.setattr(requests.Session, "post", fake_post)
    monkeypatch.setattr(requests.Session, "get", fake_get)

    data = p.generate("一只猫在键盘上", "1920x1080")
    assert data == b"\xff\xd8fake-image"
    _, post_url, payload = calls[0]
    assert "/images/generations" in post_url
    assert payload["model"] == "doubao-seedream-4-0-250828"
    assert payload["size"] == "1920x1080"          # 横版显式宽x高
    assert "output_format" not in payload           # 不传 output_format（400 坑）
    assert payload["response_format"] == "url"


def test_seedream_without_key_raises_readable_error():
    from providers.image_gen import ARKSeedreamProvider
    p = ARKSeedreamProvider({"api_key": ""})
    with pytest.raises(ValueError) as e:
        p.generate("test")
    assert "ARK API Key" in str(e.value)


# ---------------------------------------------------------------
# 视频 Provider（Seedance 异步任务状态机）
# ---------------------------------------------------------------

def test_seedance_generate_polls_until_succeeded(monkeypatch):
    from providers.video_gen import ARKSeedanceProvider

    p = ARKSeedanceProvider({"api_key": "sk-ark", "base_url": "https://ark.cn-beijing.volces.com/api/v3"})
    p.poll_interval = 0  # 测试不等待

    states = iter(["queued", "processing", "succeeded"])
    created = {"n": 0}

    def fake_post(self, url, headers=None, json=None, timeout=None):
        created["n"] += 1
        assert json["content"][0]["type"] == "text"   # content 必填（400 坑）
        assert json["duration"] == 5
        return _resp(200, {"id": "task-1"})

    def fake_get(self, url, headers=None, timeout=None):
        status = next(states)
        if status == "succeeded":
            body = {"id": "task-1", "status": "succeeded",
                    "content": {"video_url": "https://tos.xxx/v.mp4", "cover_url": "https://tos.xxx/c.jpg"}}
        else:
            body = {"id": "task-1", "status": status}
        return _resp(200, body)

    monkeypatch.setattr(requests.Session, "post", fake_post)
    monkeypatch.setattr(requests.Session, "get", fake_get)

    result = p.generate("日落时分的城市街道", 5)
    assert created["n"] == 1
    assert result["video_url"].endswith(".mp4")
    assert result["cover_url"].endswith(".jpg")


def test_seedance_failed_task_raises(monkeypatch):
    from providers.video_gen import ARKSeedanceProvider

    p = ARKSeedanceProvider({"api_key": "sk-ark", "base_url": "https://ark.cn-beijing.volces.com/api/v3"})
    p.poll_interval = 0

    def fake_post(self, url, headers=None, json=None, timeout=None):
        return _resp(200, {"id": "task-fail"})

    def fake_get(self, url, headers=None, timeout=None):
        return _resp(200, {"id": "task-fail", "status": "failed"})

    monkeypatch.setattr(requests.Session, "post", fake_post)
    monkeypatch.setattr(requests.Session, "get", fake_get)

    with pytest.raises(RuntimeError) as e:
        p.generate("test")
    assert "失败" in str(e.value)


class _resp:
    def __init__(self, code, body):
        self.status_code = code
        self._body = body

    def json(self):
        return self._body
