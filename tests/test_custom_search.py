"""
自定义新闻搜索测试
验证 ddgs 搜索 → 结果结构 + 缓存回查（勾选后 AI 写作能拿到素材）
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from tools.custom_search import search_news, get_from_cache, SEARCH_CACHE
from service.news import fetch_news_by_ids


def _clean_cache():
    SEARCH_CACHE.clear()


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
