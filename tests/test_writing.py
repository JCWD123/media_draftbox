"""
AI 写作编排测试 - parse / 图片生成 / 全流程（LLM 与图片均 mock）
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest

from service import writing
from service.writing import parse_article, generate_article, IMG_PATTERN


# ---------------------------------------------------------------
# parse_article
# ---------------------------------------------------------------

def test_parse_article_extracts_title_tags_and_placeholders():
    raw = """# AI 正在重写内容生产

正文第一段。

[IMG: 一个程序员在深夜办公桌前敲代码的特写]

第二段内容。

[VID: 城市夜景延时摄影]

标签: AI, 大模型, 效率工具
"""
    parsed = parse_article(raw, max_images=4, max_videos=1)
    assert parsed["ok"]
    assert parsed["title"] == "AI 正在重写内容生产"
    assert parsed["tags"] == ["AI", "大模型", "效率工具"]
    assert "[IMG:" in parsed["content"]
    assert "[VID:" in parsed["content"]


def test_parse_article_strips_code_block_wrapper():
    raw = """```markdown
# 标题

正文
```"""
    parsed = parse_article(raw)
    assert parsed["ok"]
    assert parsed["title"] == "标题"
    assert "```" not in parsed["content"]


def test_parse_article_truncates_excess_placeholders():
    raw = "# T\n\n" + "\n\n".join(f"[IMG: 描述{i}]" for i in range(6)) + "\n\n标签: a"
    parsed = parse_article(raw, max_images=3, max_videos=0)
    assert IMG_PATTERN.findall(parsed["content"]).__len__() == 3


def test_parse_article_removes_videos_when_disabled():
    raw = "# T\n\n段落\n\n[VID: 场景描述]\n\n标签: a"
    parsed = parse_article(raw, max_images=4, max_videos=0)
    assert "[VID:" not in parsed["content"]


# ---------------------------------------------------------------
# 图片生成（mock provider）
# ---------------------------------------------------------------

def test_generate_images_replaces_placeholders(monkeypatch, tmp_path):
    class FakeProvider:
        def generate(self, prompt, size="1920x1080"):
            return b"fake-image-bytes"

    import service.media_task as mt
    monkeypatch.setattr(mt, "IMAGES_DIR", tmp_path)
    monkeypatch.setattr("providers.get_image", lambda: FakeProvider())

    md = "段落一\n\n[IMG: 一只橘猫]\n\n段落二"
    new_md, media, warnings = writing.generate_images(md, 4, "gen_test1")
    assert "[IMG:" not in new_md
    assert "/media/images/gen_test1_1.png" in new_md
    assert len(media) == 1
    assert media[0]["source"] == "seedream"
    assert (tmp_path / "gen_test1_1.png").read_bytes() == b"fake-image-bytes"


def test_generate_images_pexels_fallback(monkeypatch, tmp_path):
    class FakeProvider:
        def generate(self, prompt, size="1920x1080"):
            raise RuntimeError("模型未开通")

    import service.media_task as mt
    monkeypatch.setattr(mt, "IMAGES_DIR", tmp_path)
    monkeypatch.setattr("providers.get_image", lambda: FakeProvider())
    monkeypatch.setattr("service.writing.search_images", lambda q, n: {"images": [{"url": "https://pexels/fallback.jpg"}]})

    md = "段落\n\n[IMG: 城市天际线]\n\n段落"
    new_md, media, warnings = writing.generate_images(md, 4, "gen_test2")
    assert "https://pexels/fallback.jpg" in new_md
    assert media[0]["source"] == "pexels"


# ---------------------------------------------------------------
# 全流程（mock LLM + 图片 + 转换）
# ---------------------------------------------------------------

class FakeReq:
    topic = "AI Agent 如何改变内容创作"
    news_ids = []
    upload_content = ""
    title = ""
    with_images = True
    with_video = False
    max_images = 2
    max_videos = 0
    skill_name = "wechat-writing"


def test_generate_article_full_flow(monkeypatch, tmp_path):
    import service.media_task as mt
    monkeypatch.setattr(mt, "IMAGES_DIR", tmp_path)

    # mock LLM
    def fake_llm(messages, model=None, timeout=120, **kw):
        return """# 测试标题

第一段内容介绍。

[IMG: 一个AI机器人在办公室]

第二段内容。

标签: AI, 效率工具
"""
    monkeypatch.setattr("service.writing.llm_chat", fake_llm)

    # mock 图片 provider
    class FakeImage:
        def generate(self, prompt, size="1920x1080"):
            return b"img-bytes"
    monkeypatch.setattr("providers.get_image", lambda: FakeImage())

    # mock 新闻回查
    monkeypatch.setattr("service.writing.fetch_news_by_ids", lambda ids: [])

    # mock 垂直度（避免真调 LLM）
    monkeypatch.setattr("service.writing.check_vertical", lambda tags, skill: _VR())
    # mock 转换（避免调 wewrite CLI）
    monkeypatch.setattr("service.writing.convert.convert_markdown",
                        lambda md, theme, video_cards=None: {"html": f"<div>{md}</div>", "theme": theme})

    class _VR:
        drifted = False
        domain = "科技AI"
        note = "一致"

    result = generate_article(FakeReq())
    assert result["success"]
    assert result["title"] == "测试标题"
    assert result["tags"] == ["AI", "效率工具"]
    assert "[IMG:" not in result["content"]
    assert result["media"]["images"]
    assert result["skill_version"] >= 1


def test_generate_article_rejects_empty_topic(monkeypatch):
    req = FakeReq()
    req.topic = "  "
    result = generate_article(req)
    assert not result["success"]
    assert "话题" in result["error"]
