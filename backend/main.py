"""
DraftBox 后端入口 - 参考 hermes-agent 架构
"""
import sys
import threading
import time
from pathlib import Path

# 添加 backend 目录到 Python 路径
backend_dir = Path(__file__).parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from api import news, convert, grammar, images, drafts, plugins, execute, write, skill, illustrate
from providers import init_registry
from service.media_task import MEDIA_DIR

# 初始化三套 Provider（LLM / 图片 / 视频），配置读 ~/.draftbox/config.yaml
init_registry()

app = FastAPI(title="DraftBox API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(news.router, prefix="/api/news", tags=["新闻"])
app.include_router(convert.router, prefix="/api", tags=["转换"])
app.include_router(grammar.router, prefix="/api/grammar", tags=["语法检查"])
app.include_router(images.router, prefix="/api/images", tags=["图片搜索"])
app.include_router(drafts.router, prefix="/api/drafts", tags=["草稿管理"])
app.include_router(plugins.router, prefix="/api/system", tags=["系统"])
app.include_router(execute.router, prefix="/api/execute", tags=["代码执行"])
app.include_router(write.router, prefix="/api", tags=["AI写作"])
app.include_router(skill.router, prefix="/api", tags=["Skill进化"])
app.include_router(illustrate.router, prefix="/api/illustrate", tags=["文章配图"])

# 生成的媒体文件静态服务（/media/images/xxx.png 等）
MEDIA_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=str(MEDIA_DIR)), name="media")


# ---------------- 无感进化定时任务（每小时检查学习目标，每天实际抓取） ----------------

def _auto_learn_loop():
    """后台线程：每小时检查一次，有学习目标且模型已配置时自动学习新文章"""
    from utils.config import load_config

    while True:
        try:
            cfg = load_config()
            if cfg.get("model", {}).get("api_key"):
                from service import skill_engine
                skill_engine.auto_learn_once()
        except Exception:
            pass  # 定时任务失败静默，不影响主服务
        time.sleep(3600)


@app.on_event("startup")
async def startup():
    threading.Thread(target=_auto_learn_loop, daemon=True, name="draftbox-auto-learn").start()


@app.get("/health")
async def health():
    return {"status": "ok"}
