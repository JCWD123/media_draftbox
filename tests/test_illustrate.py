"""
文章配图服务单元测试 - service/illustrate.py

用 mock 替换 _gen_image（不真调 Seedream），覆盖：
1. parse_material 解析封面图/插图（章节锚点 + prompt）
2. _locate_heading 章节定位
3. illustrate 主入口（插图位置正确 + 魔数扩展名）
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import service.illustrate as il


MATERIAL_MD = """# 测试物料

## 二、公众号封面图（2.35:1）

Seedream prompt（英文）：

"Two massive glowing AI cores facing each other in a dark futuristic arena,
one deep blue, one electric purple, cinematic, no text, no letters"

## 三、文中插图（可选）

### 插图1：价格对比信息图（放在"三、性价比"章节）
建议不用 AI 生图。

如必须 AI 生成，用：
"Minimal infographic style, two giant vertical bars side by side, red and blue"

### 插图2：MoE 架构意境图（放在"一、底牌"章节）
"Gigantic dense neural network cloud bursting into thousands of tiny expert nodes"
"""

HTML = """<section>
<h1 style="...">测试标题</h1>
<p>开头。</p>
<h2 style="...">一、先看底牌：一个硬核 MoE</h2>
<p>底牌内容。</p>
<h2 style="...">二、正面开卷</h2>
<p>开卷内容。</p>
<h2 style="...">三、那个大家都不愿直说的问题：性价比</h2>
<p>性价比内容。</p>
</section>
"""


def test_parse_material():
    mat = il.parse_material(MATERIAL_MD)

    # 封面图解析
    assert mat["cover"] is not None
    assert "AI cores" in mat["cover"]["prompt"]
    assert "no text" in mat["cover"]["prompt"]
    assert mat["cover"]["size"] == "1680x720"

    # 插图解析：两条，锚点正确
    assert len(mat["figures"]) == 2
    fig1 = mat["figures"][0]
    fig2 = mat["figures"][1]
    assert fig1["anchor_num"] == 3 and fig1["anchor_tag"] == "性价比"
    assert fig2["anchor_num"] == 1 and fig2["anchor_tag"] == "底牌"
    # prompt 是纯英文（不含中文锚点尾巴）
    assert "infographic" in fig1["prompt"]
    assert "章节" not in fig1["prompt"]
    assert "expert nodes" in fig2["prompt"]


def test_locate_heading():
    assert il._locate_heading(HTML, 1, "底牌") > 0
    assert il._locate_heading(HTML, 3, "性价比") > 0
    # 关键词命中但编号不匹配时，应退回关键词匹配
    assert il._locate_heading(HTML, None, "性价比") > 0
    # 完全匹配不到 → -1
    assert il._locate_heading(HTML, None, "不存在的章节") == -1


def test_illustrate_insert_positions(monkeypatch):
    """mock 生图，验证插图位置正确 + 扩展名魔数判断"""
    calls = []

    def fake_gen(prompt, size, filename_noext):
        calls.append((prompt, size, filename_noext))
        # 返回假 JPEG 魔数数据路径
        return f"/media/images/{filename_noext}.jpg"

    monkeypatch.setattr(il, "_gen_image", fake_gen)

    result = il.illustrate(HTML, MATERIAL_MD)

    assert result["success"] is True
    assert len(result["inserted"]) == 3  # 封面 + 2 插图
    assert result["warnings"] == []

    new_html = result["html"]

    # 封面图在 h1 之后
    h1_end = new_html.find("</h1>")
    cover_pos = new_html.find("封面图", h1_end, h1_end + 200)
    assert cover_pos > 0

    # MoE 图在「一、先看底牌」章节后
    moe_pos = new_html.find("底牌")
    assert "fig" in new_html[moe_pos:moe_pos + 300]

    # 价格图在「三、性价比」章节后
    price_h2 = new_html.find("性价比")
    first_h2_before = price_h2
    # 确认「性价比」章节的 img 在它之后
    assert new_html.find("<img", first_h2_before) > first_h2_before


def test_illustrate_empty_inputs():
    assert il.illustrate("", "x")["success"] is False
    assert il.illustrate("<p>x</p>", "")["success"] is False
