"""
精品排版引擎 - 对标「学长十一的随笔」公众号风格
- 650px 限宽，阅读舒适
- 深蓝点缀 + 宋体大标题
- 2 倍行高，充足留白（text-align:justify）
- 数据卡片 / 引用块精致化
- 全部内联样式（微信公众号粘贴兼容）
"""
import re
import html as html_lib

# 主题色板
COLOR_TEXT = "#253047"
COLOR_TITLE = "#172033"
COLOR_ACCENT = "#1f4ed8"
COLOR_MUTED = "#596273"
COLOR_BORDER = "#e6ebf3"
COLOR_BG_SOFT = "#f5f7fb"
COLOR_SERIF = "Songti SC,STSong,serif"


def _h1(text):
    s = "margin:0 0 20px;font-size:26px;line-height:1.5;font-weight:700;color:" + COLOR_TITLE + ";letter-spacing:.01em;"
    return '<h1 style="' + s + '">' + text + '</h1>'


def _h2(text):
    s = ("margin:36px 0 18px;font-size:22px;line-height:1.5;font-weight:700;color:" + COLOR_TITLE
         + ";padding-left:14px;border-left:4px solid " + COLOR_ACCENT + ";")
    return '<h2 style="' + s + '">' + text + '</h2>'


def _h3(text):
    s = "margin:30px 0 14px;font-size:18px;line-height:1.5;font-weight:600;color:" + COLOR_TITLE + ";"
    return '<h3 style="' + s + '">' + text + '</h3>'


def _p(inner):
    s = ("margin:0 0 18px;font-size:16px;line-height:2;color:" + COLOR_TEXT
         + ";text-align:justify;letter-spacing:.02em;")
    return '<p style="' + s + '">' + inner + '</p>'


def _blockquote(inner):
    s = ("margin:24px 0;padding:16px 20px;border-left:4px solid " + COLOR_ACCENT
         + ";background:" + COLOR_BG_SOFT + ";border-radius:8px;color:" + COLOR_TEXT
         + ";font-size:15px;line-height:1.9;")
    return '<blockquote style="' + s + '">' + inner + '</blockquote>'


def _ul(items):
    li = ""
    for t in items:
        li += '<li style="margin:8px 0;line-height:1.9;color:' + COLOR_TEXT + ';list-style:none;">' + t + '</li>'
    return '<ul style="margin:18px 0 24px;padding-left:0;list-style:none;">' + li + '</ul>'


def _ol(items):
    li = ""
    for i, t in enumerate(items, 1):
        li += ('<li style="margin:10px 0;line-height:1.9;color:' + COLOR_TEXT + ';">'
               + '<span style="color:' + COLOR_ACCENT + ';font-weight:600;margin-right:10px;">' + str(i) + '.</span>'
               + t + '</li>')
    return '<ol style="margin:18px 0 24px;padding-left:0;list-style:none;">' + li + '</ol>'


def _code_inline(text):
    s = "background:" + COLOR_BG_SOFT + ";padding:2px 6px;border-radius:4px;font-size:14px;color:" + COLOR_ACCENT + ";"
    return '<code style="' + s + '">' + text + '</code>'


def _code_block(text):
    s = ("margin:20px 0 26px;padding:18px 20px;background:" + COLOR_TITLE + ";border-radius:10px;"
         + "overflow-x:auto;line-height:1.7;")
    cs = "color:#e2e8f0;font-size:14px;display:block;"
    return ('<pre style="' + s + '"><code style="' + cs + '">' + html_lib.escape(text) + '</code></pre>')


def _table(headers, rows):
    thead = ""
    for h in headers:
        thead += ('<th style="padding:12px 14px;background:' + COLOR_BG_SOFT + ';font-weight:600;color:'
                  + COLOR_TITLE + ';text-align:left;font-size:14px;">' + h + '</th>')
    trs = ""
    for r in rows:
        tds = ""
        for c in r:
            tds += ('<td style="padding:12px 14px;border-bottom:1px solid ' + COLOR_BORDER + ';color:'
                    + COLOR_TEXT + ';font-size:14px;line-height:1.8;">' + c + '</td>')
        trs += '<tr>' + tds + '</tr>'
    ts = "border-collapse:collapse;width:100%;border-top:1px solid " + COLOR_BORDER + ";border-bottom:1px solid " + COLOR_BORDER + ";"
    return ('<table style="margin:22px 0 28px;' + ts + '"><thead><tr>' + thead + '</tr></thead><tbody>'
            + trs + '</tbody></table>')


def _img(src, alt=""):
    s = "max-width:100%;height:auto;border-radius:10px;margin:20px 0;display:block;"
    return '<img src="' + html_lib.escape(src) + '" alt="' + html_lib.escape(alt) + '" style="' + s + '"/>'


def _link(href, text):
    s = "color:" + COLOR_ACCENT + ";text-decoration:none;"
    return '<a href="' + html_lib.escape(href) + '" style="' + s + '">' + text + '</a>'


def _hr():
    s = "border:none;border-top:1px solid " + COLOR_BORDER + ";margin:36px 0;"
    return '<hr style="' + s + '"/>'


def _stat_card(items):
    content = ""
    for k, v in items:
        content += ('<div style="flex:1;text-align:center;padding:14px 8px;min-width:110px;">'
                    + '<div style="font-size:28px;font-weight:700;color:' + COLOR_ACCENT + ';line-height:1.2;">'
                    + html_lib.escape(v) + '</div>'
                    + '<div style="font-size:13px;color:' + COLOR_MUTED + ';margin-top:6px;">'
                    + html_lib.escape(k) + '</div></div>')
    s = ("margin:28px 0 42px;padding:24px 12px;border:1px solid " + COLOR_BORDER
         + ";border-radius:14px;background:#ffffff;display:flex;flex-wrap:wrap;gap:8px;")
    return '<section style="' + s + '">' + content + '</section>'


def _shell(body):
    s = ("max-width:650px;margin:0 auto;padding:24px 0;font-family:-apple-system,BlinkMacSystemFont,"
         + 'Segoe UI,PingFang SC,Microsoft YaHei,sans-serif";')
    # 注意：max-width 是微信容器，内层字体用中文优先
    s = ("max-width:650px;margin:0 auto;padding:24px 0;"
         + 'font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;')
    return '<section style="' + s + '">' + body + '</section>'


# ---- 行内解析 ----
_INLINE_RE = re.compile(
    r"(`[^`]+`|\[([^\]]+)\]\(([^)]+)\)|\*\*([^*]+)\*\*|\*([^*]+)\*|!\[([^\]]*)\]\(([^)]+)\))")


def _inline(text):
    """行内元素渲染"""
    def repl(m):
        g0 = m.group(1)
        if g0.startswith("`"):
            return _code_inline(g0[1:-1])
        if g0.startswith("!"):
            return _img(m.group(7), m.group(6))
        if m.group(2):
            return _link(m.group(3), _inline(m.group(2)))
        if m.group(4):
            strong = "color:" + COLOR_TEXT + ";font-weight:700;"
            return '<strong style="' + strong + '">' + _inline(m.group(4)) + '</strong>'
        if m.group(5):
            em = "color:" + COLOR_TEXT + ";font-style:italic;"
            return '<em style="' + em + '">' + _inline(m.group(5)) + '</em>'
        return g0
    return _INLINE_RE.sub(repl, html_lib.escape(text))


def _parse_table(lines, i):
    """解析 markdown 表格为统计卡片或 HTML 表格。
    返回 (html, next_i)，next_i 指向表格后的下一行。
    """
    start = i
    rows = []
    while i < len(lines) and lines[i].strip().startswith("|"):
        cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
        rows.append(cells)
        i += 1
    if not rows:
        return None, i
    # 跳过表头分隔行
    if len(rows) > 1 and re.match(r"^[\s:\-|]+$", "|".join(rows[1])):
        rows.pop(1)
    if not rows or not rows[0]:
        return None, i
    header = rows[0]
    data = rows[1:]
    # 两列表 → 统计卡片
    if data and len(data[0]) == 2 and len(header) == 2:
        items = [(r[0], r[1]) for r in data]
        return _stat_card(items), i
    # 通用表格
    return _table(header, data), i


def render(markdown_text: str) -> str:
    """markdown → 精品排版 HTML（内联样式，微信兼容）"""
    lines = markdown_text.split("\n")
    out = []
    i = 0
    in_code = False
    code_buf = []
    list_type = None
    items = []

    while i < len(lines):
        stripped = lines[i].strip()

        if stripped.startswith("```"):
            if not in_code:
                in_code, code_buf = True, []
            else:
                in_code = False
                out.append(_code_block("\n".join(code_buf)))
            i += 1
            continue
        if in_code:
            code_buf.append(lines[i])
            i += 1
            continue

        if stripped.startswith("|"):
            card, i = _parse_table(lines, i)
            if card:
                out.append(card)
            continue

        # 列表
        if re.match(r"^[-*]\s+", stripped) or re.match(r"^\d+[.、]\s+", stripped):
            if list_type is None:
                list_type = "ol" if re.match(r"^\d+", stripped) else "ul"
                items = []
            item = re.sub(r"^[-*]\s+|\d+[.、]\s+", "", stripped)
            items.append(_inline(item))
            i += 1
            continue
        if list_type is not None:
            out.append(_ol(items) if list_type == "ol" else _ul(items))
            list_type, items = None, []

        if stripped.startswith("# "):
            out.append(_h1(_inline(stripped[2:])))
        elif stripped.startswith("## "):
            out.append(_h2(_inline(stripped[3:])))
        elif stripped.startswith("### "):
            out.append(_h3(_inline(stripped[4:])))
        elif stripped.startswith("> "):
            out.append(_blockquote(_inline(stripped[2:])))
        elif stripped == "---":
            out.append(_hr())
        elif not stripped:
            out.append("")
        else:
            out.append(_p(_inline(stripped)))

        i += 1

    if list_type is not None:
        out.append(_ol(items) if list_type == "ol" else _ul(items))

    return _shell("\n".join(out))
