"""
DraftBox 后端入口 - 参考 hermes-agent 架构
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import news, convert, grammar, images, drafts, plugins, execute

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


@app.get("/health")
async def health():
    return {"status": "ok"}
