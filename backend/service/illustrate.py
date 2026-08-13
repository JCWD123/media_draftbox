"""
文章配图服务 - 根据「发布物料.md」的规则给现成 HTML 精确插入图片

物料.md 里定义了插图规则：
  cover:  封面图（插到 <h1> 之后）
  figure: 正文插图（插到对应 <h2> 章节之后），通过「章节锚点」匹配

锚点匹配策略：
  物料里写的「三、性价比」章节，HTML 里是 <h2>三、那个大家都不愿直说的问题：性价比</h2>
  用「章节序号（一/二/三…）」+ 提取的「关键词」做模糊匹配，
  取编号相同 且 关键词命中 的 <h2>；编号不明确时退化为「关键词命中」排序第一。

流程：解析物料 → 逐条生图(Seedream) → 存 media/images → 把 <img> 插到 HTML 对应位置
"""
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from service.media_task import IMAGES_DIR


# ---------------------------------------------------------------
# 素材解析
# ---------------------------------------------------------------

# 中文序号 → 阿拉伯数字
_CN_NUM = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}

# 章节锚点描述 → 用于匹配 h2 的关键词（按「封面/插图N」小节标题里的括号或标题文本提取）
_CHAPTER_HINT = {
    "底牌": ["底牌"],
    "正面开卷": ["正面开卷", "开卷"],
    "性价比": ["性价比"],
    "坑": ["坑", "别被数字骗"],
    "选谁": ["选谁", "到底选"],
}


def _parse_number(s: str):
    """从「三、那个...」「第三、」「插图1」提取序号数字，找不到返回 None"""
    m = re.search(r"^[（(]?([一二三四五六七八九十\d]+)", s)
    if m:
        t = m.group(1)
        if t.isdigit():
            return int(t)
        if t in _CN_NUM:
            return _CN_NUM[t]
    return None


def _extract_prompt(text: str) -> str:
    """从物料小节中提取 Seedream prompt。

    取小节里「最长的」双引号块（英文长文本才是 prompt），
    避免误取「建议不用 AI 生图」「输出 6美元…」这类短中文引号块。
    支持半角 " 和全角 中文双引号。
    """
    # 真正的 Seedream prompt 是「纯英文长文本」（多行）。
    # 中文混合文本里半角引号无法区分开闭，容易错误配对，
    # 因此直接用「最长连续英文段」作为 prompt——更稳健。
    # 抓出所有英文为主的长段（字母+空格+标点），取最长的一段。
    en_runs = re.findall(r'[A-Za-z][A-Za-z0-9,.\'"()\[\]:;/%+-]*(?:\s+[A-Za-z0-9,.\'"()\[\]:;/%+-]+){8,}', text)
    best = ""
    for run in en_runs:
        run = run.strip().strip('"“”')
        if len(run) > len(best):
            best = run
    return best


def _parse_anchor(title_line: str):
    """从插图标题行提取 (序号, 章节关键词)。如「插图1：价格对比信息图（放在"三、性价比"章节）」

    返回 (anchor_num, anchor_tag)，锚点可能缺序号或关键词时对应为 None / 空串。
    """
    anchor_num = None
    anchor_tag = ""
    # 匹配「N、关键词」或「第N章节」等，引号半角全角都兼容
    m = re.search(r'[“"「]([一二三四五六七八九十\d]+)[、.．·]?\s*([^”"」]{1,8}?)(?:章节)?[”"」]', title_line)
    if m:
        anchor_num = _parse_number(m.group(1))
        anchor_tag = m.group(2).strip()
    return anchor_num, anchor_tag


def parse_material(md: str) -> Dict:
    """解析发布物料.md → {cover: {prompt,size}, figures: [{index, anchor, prompt, size, label}]}"""
    md = md or ""
    cover = None
    figures: List[Dict] = []
    size = "1920x1080"

    # 定位「封面图」小节 → 提取最长引号块作 cover
    cover_block = ""
    m = re.search(r"封面图[^\n]*\n(.*?)(?=\n## |\Z)", md, re.DOTALL)
    if m:
        cover_block = m.group(1)

    # 「文中插图」之后的所有内容
    figs_section = re.search(r"文中插图.*?\n(.*)$", md, re.DOTALL)
    figs_text = figs_section.group(1) if figs_section else ""

    # 按 ### 插图 拆分
    parts = re.split(r"(?=###\s*插图)", figs_text)

    for part in parts:
        part = part.strip()
        if not part:
            continue
        title_line = part.splitlines()[0] if part.splitlines() else ""
        prompt = _extract_prompt(part)
        if not prompt:
            continue

        label = re.sub(r"^###\s*插图\d*[:：]?", "", title_line).strip() or "插图"
        # 去掉「（放在…章节）」尾巴，让 label 更干净
        label = re.sub(r"[（(].*?[）)]$", "", label).strip() or label

        anchor_num, anchor_tag = _parse_anchor(title_line)

        figures.append({
            "label": label[:40],
            "anchor_num": anchor_num,
            "anchor_tag": anchor_tag,
            "prompt": prompt,
            "size": size,
        })

    # 封面图
    cover_prompt = _extract_prompt(cover_block)
    if cover_prompt:
        cover = {"prompt": cover_prompt, "size": "1680x720"}  # 封面 2.35:1 横幅

    return {"cover": cover, "figures": figures}


# ---------------------------------------------------------------
# 章节定位
# ---------------------------------------------------------------

_H2_RE = re.compile(r"<h2[^>]*>(.*?)</h2>", re.DOTALL)
_TAG_RE = re.compile(r"<[^>]+>")


def _h2_text(h2_html: str) -> str:
    """去掉 h2 里的标签和序号前缀，得到纯文本供匹配"""
    text = _TAG_RE.sub("", h2_html).strip()
    # 去掉开头的「一、」「二、」「第三、」等序号前缀，便于关键词匹配
    text = re.sub(r"^[一二三四五六七八九十\d]+[、.．\s]*", "", text)
    return text


def _locate_heading(html: str, anchor_num, anchor_tag: str) -> int:
    """在 html 中定位目标 <h2> 的结束位置（即插图应插入的位置）。返回字符索引，失败返回 -1"""
    matches = list(_H2_RE.finditer(html))
    if not matches:
        return -1

    candidates = []
    for idx, m in enumerate(matches):
        text = _h2_text(m.group(0))
        text_num = None
        mm = re.match(r"^([一二三四五六七八九十\d]+)", m.group(0).replace("<h2", " ").replace("style", ""))
        # 从原始 h2 文本里提序号（去掉标签后）
        raw = _TAG_RE.sub("", m.group(0)).strip()
        nm = re.match(r"^([一二三四五六七八九十\d]+)", raw)
        if nm:
            text_num = _parse_number(nm.group(1))

        # 关键词命中
        kw_hit = False
        if anchor_tag:
            kw_hit = anchor_tag in text
        candidates.append({"idx": idx, "end": m.end(), "text": text, "num": text_num, "kw_hit": kw_hit})

    # 优先级 1：编号相同 且 关键词命中
    if anchor_num is not None:
        for c in candidates:
            if c["num"] == anchor_num and c["kw_hit"]:
                return c["end"]
        # 优先级 2：编号相同（关键词没命中，退一步）
        for c in candidates:
            if c["num"] == anchor_num and (not anchor_tag or anchor_tag in c["text"]):
                return c["end"]

    # 优先级 3：关键词命中（编号对不上时）
    if anchor_tag:
        for c in candidates:
            if c["kw_hit"]:
                return c["end"]

    return -1


# ---------------------------------------------------------------
# 生图 + 插图
# ---------------------------------------------------------------

def _build_img_tag(url: str, alt: str) -> str:
    """微信兼容的 <img> 内联样式标签"""
    alt = (alt or "").replace('"', "'")
    return (
        f'<p style="text-align:center;margin:20px 0;">'
        f'<img src="{url}" alt="{alt}" style="max-width:100%;height:auto;border-radius:4px;">'
        f'</p>'
    )


def _gen_image(prompt: str, size: str, filename_noext: str):
    """调 Seedream 生图，存磁盘，返回 /media/images/<name>；失败抛异常。

    Seedream 实际返回 JPEG 数据（尽管 size 参数通用），
    这里按文件魔数自动定扩展名（.jpg/.png），避免 .png 名配 JPEG 体。
    """
    from providers import get_image
    provider = get_image()
    data = provider.generate(prompt, size)
    ext = ".jpg" if data[:3] == b"\xff\xd8\xff" else ".png"
    path = IMAGES_DIR / f"{filename_noext}{ext}"
    path.write_bytes(data)
    return f"/media/images/{path.name}"


def illustrate(html: str, material_md: str) -> Dict:
    """主入口：给 html 按物料配图，返回 {html, inserted, warnings}"""
    if not html or not html.strip():
        return {"success": False, "error": "文章 HTML 为空"}
    if not material_md or not material_md.strip():
        return {"success": False, "error": "发布物料.md 为空"}

    mat = parse_material(material_md)
    if not mat["cover"] and not mat["figures"]:
        return {"success": False, "error": "未能从物料.md 解析出任何插图规则（封面图/插图均无 prompt）"}

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    inserted: List[Dict] = []
    warnings: List[str] = []
    new_html = html

    # 1. 封面图 → 插到 <h1> 之后
    if mat["cover"]:
        try:
            url = _gen_image(mat["cover"]["prompt"], mat["cover"]["size"], f"{ts}_cover")
            m = re.search(r"<h1[^>]*>.*?</h1>", new_html, re.DOTALL)
            if m:
                tag = _build_img_tag(url, "封面图")
                new_html = new_html[:m.end()] + tag + new_html[m.end():]
                inserted.append({"label": "封面图", "position": "h1后", "url": url, "ok": True})
            else:
                warnings.append("封面图：未找到 <h1>，跳过")
        except Exception as e:
            warnings.append(f"封面图生成失败: {str(e)[:120]}")

    # 2. 正文插图 → 插到对应 <h2> 章节之后
    for i, fig in enumerate(mat["figures"], 1):
        pos = _locate_heading(new_html, fig["anchor_num"], fig["anchor_tag"])
        if pos < 0:
            warnings.append(f"插图「{fig['label']}」未定位到章节（锚点：{fig['anchor_tag'] or fig['anchor_num']}），跳过")
            continue
        try:
            url = _gen_image(fig["prompt"], fig["size"], f"{ts}_fig{i}")
            tag = _build_img_tag(url, fig["label"])
            new_html = new_html[:pos] + tag + new_html[pos:]
            inserted.append({"label": fig["label"], "position": "章节后", "url": url, "ok": True})
        except Exception as e:
            warnings.append(f"插图「{fig['label']}」生成失败: {str(e)[:120]}")

    return {
        "success": True,
        "html": new_html,
        "inserted": inserted,
        "warnings": warnings,
    }
