"""
转换服务 - wewrite 引擎
"""
import subprocess
import os
from pathlib import Path


def convert_markdown(markdown: str, theme: str):
    """Markdown → 微信兼容 HTML"""
    tmp_md = "/tmp/draftbox_input.md"
    with open(tmp_md, "w", encoding="utf-8") as f:
        f.write(markdown)

    subprocess.run(
        ["wewrite", "preview", tmp_md, "-t", theme, "-o", "/tmp/draftbox_output.html", "--no-open"],
        timeout=30
    )

    if os.path.exists("/tmp/draftbox_output.html"):
        with open("/tmp/draftbox_output.html", encoding="utf-8") as f:
            return {"html": f.read(), "theme": theme}

    return {"error": "转换失败"}


def get_themes():
    """获取主题列表"""
    themes_dir = Path(__file__).parent.parent / "src" / "wewrite" / "src" / "wewrite" / "toolkit" / "themes"
    if themes_dir.exists():
        return {"themes": [{"id": f.stem, "name": f.stem} for f in themes_dir.glob("*.yaml")]}
    return {"themes": []}
