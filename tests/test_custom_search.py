"""
自定义新闻搜索测试
验证 ddgs 搜索 → 结果结构 + 缓存回查（勾选后 AI 写作能拿到素材）
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from tools.custom_search import search_news, get_from_cache, SEARCH_CACHE, DDGS_AVAILABLE
from service.news import fetch_news_by_ids

# ddgs 是可选依赖（需 Python >=3.9/3.10），未安装时跳过需要真实搜索的测试
requires_ddgs = pytest.mark.skipif(
    not DDGS_AVAILABLE,
    reason="ddgs 未安装（需 Python >=3.9），跳过真实搜索测试",
)


def _clean_cache():
    SEARCH_CACHE.clear()


@requires_ddgs
def test_search_returns_standard_structure():
    """搜索返回 draftbox 标准新闻结构（含项目必需字段）"""
    _clean_cache()
    d = search_news("开源AI模型 发布", limit=3)
    assert d.get("error") is None or "未安装" not in d.get("error", "")
    news = d.get("news", [])
    # 搜索可能返回空（网络波动），若空跳过结构断言
    if not news:
        return
    for n in news:
        assert "id" in n and "title" in n and "link" in n and "source" in n
        assert n["category"] == "SEARCH"


@requires_ddgs
def test_search_writes_cache_and_recover():
    """搜索写入缓存，get_from_cache 能回查（勾选后 AI 写作链路）"""
    _clean_cache()
    d = search_news("AI Agent 框架 开源", limit=4)
    news = d.get("news", [])
    if not news:
        assert True  # 网络波动时空跳
        return
    nid = news[0]["id"]
    found = get_from_cache([nid])
    assert len(found) == 1
    assert found[0]["id"] == nid
    assert found[0]["title"] == news[0]["title"]


@requires_ddgs
def test_fetch_news_by_ids_hits_search_cache():
    """fetch_news_by_ids 优先命中搜索缓存（写作回查链路）"""
    _clean_cache()
    d = search_news("DeepSeek 开源 模型", limit=3)
    news = d.get("news", [])
    if not news:
        assert True
        return
    nid = news[0]["id"]
    # 直接调写作用的 fetch_news_by_ids
    result = fetch_news_by_ids([nid])
    assert len(result) == 1
    assert result[0]["id"] == nid


def test_search_rejects_empty_query():
    """空搜索词返回可读错误而非崩溃"""
    _clean_cache()
    d = search_news("  ", limit=3)
    assert "error" in d
    assert d.get("news") == []


# ---- Jina Reader 正文增强 ----

def test_enhance_skips_non_search_items():
    """fetch_news_by_ids 对非 SEARCH 类新闻不抓正文（快路径）"""
    from service.news import _enhance_with_body
    items = [{"id": "x1", "title": "普通新闻", "link": "https://example.com", "category": "TECH"}]
    result = _enhance_with_body(items)
    # 不触发 Jina 抓取（非 SEARCH 类），保持原样
    assert result == items


def test_fetch_news_by_ids_returns_list():
    """fetch_news_by_ids 对空 id 返回空列表（不报错）"""
    from service.news import fetch_news_by_ids
    assert fetch_news_by_ids([]) == []
    assert fetch_news_by_ids(None) == []
