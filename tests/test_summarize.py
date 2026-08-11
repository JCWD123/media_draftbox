"""
新闻 AI 摘要服务测试
验证 summarize 的输入准备 / LLM 调用 / 错误处理
"""
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from service.summarize import summarize, _build_content


def _fake_llm(messages, model=None, timeout=None, **kw):
    """mock LLM：返回固定摘要（真实 llm_chat 返回纯字符串）"""
    return "这是一段用于测试的核心新闻摘要内容。"


def test_summarize_uses_existing_body():
    """有已有正文(summary)时，进入 LLM 调用并返回摘要"""
    with patch("service.summarize.llm_chat", side_effect=_fake_llm):
        r = summarize("测试新闻标题", "这是一条足够长的正文内容，超过三十个字符以便满足已有正文的分支判断条件。", "")
    assert r["success"] is True
    assert "核心新闻摘要" in r["summary"]
    assert r.get("source") == "已有正文"


def test_summarize_missing_title():
    """缺标题返回可读错误"""
    r = summarize("")
    assert r["success"] is False
    assert "标题" in r["error"]


def test_build_content_uses_body_when_long():
    """正文足够长直接采用"""
    body = "x" * 50
    content, source = _build_content("标题", body, "")
    assert source == "已有正文"
    assert content == body[:2000]


def test_build_content_falls_to_title():
    """正文不足且无链接时降级为仅标题"""
    content, source = _build_content("仅标题有内容", "", "")
    assert source == "仅标题"
    assert content == "仅标题有内容"


def test_summarize_llm_failure_returns_error():
    """LLM 抛错时返回可读错误"""
    def _boom(messages, model=None, timeout=None, **kw):
        raise RuntimeError("模型不可用")
    with patch("service.summarize.llm_chat", side_effect=_boom):
        r = summarize("测试", "正文内容够长用于触发LLM调用调用调用调用调用", "")
    assert r["success"] is False
    assert "模型不可用" in r["error"]
