"""
媒体后台任务测试 - 视频任务状态机（mock 视频 provider）
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest

from service import media_task


def _wait_status(draft_id, expect, timeout=10):
    """轮询直到状态满足"""
    deadline = time.time() + timeout
    while time.time() < deadline:
        st = media_task.get_video_status(draft_id)
        if st["status"] == expect:
            return st
        time.sleep(0.1)
    return media_task.get_video_status(draft_id)


def test_video_task_runs_and_calls_on_done(monkeypatch):
    monkeypatch.setattr(media_task, "TASKS_FILE", Path(__file__).parent / "_tasks_test.json")

    class FakeVideo:
        def generate(self, prompt, duration=5):
            return {"task_id": "t1", "video_url": "https://tos.xxx/v.mp4", "cover_url": "https://tos.xxx/c.jpg"}

    monkeypatch.setattr("providers.get_video", lambda: FakeVideo())
    monkeypatch.setattr("requests.Session.get", lambda self, url, timeout=None: _bytes_resp(b"fake-mp4"))

    called = []

    def on_done(draft_id):
        called.append(draft_id)

    media_task.enqueue_video_generation("test_v1", [{"idx": 1, "prompt": "城市夜景"}], on_done=on_done)
    st = _wait_status("test_v1", "done")
    assert st["status"] == "done"
    assert len(st["videos"]) == 1
    assert st["videos"][0]["path"].endswith("test_v1_1.mp4")
    assert called == ["test_v1"]


def test_video_task_failed_records_error(monkeypatch):
    monkeypatch.setattr(media_task, "TASKS_FILE", Path(__file__).parent / "_tasks_test2.json")

    class FakeVideo:
        def generate(self, prompt, duration=5):
            raise RuntimeError("模型未开通")

    monkeypatch.setattr("providers.get_video", lambda: FakeVideo())

    media_task.enqueue_video_generation("test_v2", [{"idx": 1, "prompt": "x"}])
    st = _wait_status("test_v2", "failed")
    assert st["status"] == "failed"
    assert "未开通" in st["error"]


class _bytes_resp:
    def __init__(self, content):
        self.status_code = 200
        self.content = content
