"""
数据模型 - Pydantic 校验
防止 SQL 注入、XSS 攻击等安全问题
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
import re


class ConvertRequest(BaseModel):
    """转换请求模型"""
    markdown: str = Field(..., min_length=1, max_length=100000, description="Markdown 内容")
    theme: str = Field(default="professional-clean", max_length=50)

    @field_validator("markdown")
    @classmethod
    def validate_markdown(cls, v):
        # 过滤危险内容
        if re.search(r"<script|javascript:|on\w+\s*=", v, re.IGNORECASE):
            raise ValueError("包含危险内容")
        return v.strip()

    @field_validator("theme")
    @classmethod
    def validate_theme(cls, v):
        allowed = ["premium", "professional", "minimal", "github", "newspaper", "bold-navy",
                   "professional-clean", "bauhaus", "bold-green", "bytedance",
                   "elegant-rose", "focus-red", "impeccable", "ink", "lobster-notes",
                   "midnight", "minimal-gold", "sspai", "tech-modern", "warm-editorial"]
        if v not in allowed:
            raise ValueError(f"主题必须是以下之一: {allowed}")
        return v


class DraftSaveRequest(BaseModel):
    """草稿保存请求模型"""
    title: str = Field(..., min_length=1, max_length=100, description="草稿标题")
    content: str = Field(..., min_length=1, max_length=500000, description="Markdown 源内容")
    html: str = Field(default="", max_length=1000000, description="wewrite 排版后的 HTML（可选）")

    @field_validator("title")
    @classmethod
    def validate_title(cls, v):
        # 过滤特殊字符
        v = re.sub(r'[<>:"/\\|?*]', "", v)
        return v.strip()[:50]

    @field_validator("content")
    @classmethod
    def validate_content(cls, v):
        # 过滤危险内容
        if re.search(r"<script|javascript:", v, re.IGNORECASE):
            raise ValueError("包含危险内容")
        return v


class GrammarCheckRequest(BaseModel):
    """语法检查请求模型"""
    text: str = Field(..., min_length=1, max_length=10000, description="待检查文本")
    language: str = Field(default="zh", max_length=10)

    @field_validator("language")
    @classmethod
    def validate_language(cls, v):
        allowed = ["zh", "en", "ja", "ko", "fr", "de", "es"]
        if v not in allowed:
            raise ValueError(f"语言必须是以下之一: {allowed}")
        return v


class ImageSearchRequest(BaseModel):
    """图片搜索请求模型"""
    query: str = Field(..., min_length=1, max_length=100, description="搜索关键词")
    count: int = Field(default=12, ge=1, le=50, description="返回数量")

    @field_validator("query")
    @classmethod
    def validate_query(cls, v):
        # 过滤特殊字符
        v = re.sub(r'[<>:"/\\|?*]', "", v)
        return v.strip()


class NewsRequest(BaseModel):
    """新闻请求模型"""
    category: str = Field(default="TECH", max_length=20)
    page: int = Field(default=1, ge=1, le=100)
    page_size: int = Field(default=20, ge=1, le=100)

    @field_validator("category")
    @classmethod
    def validate_category(cls, v):
        allowed = ["FINANCE", "TECH", "SOCIAL", "DEVELOPER", "VIDEO", "COMMUNITY", "KNOWLEDGE"]
        if v not in allowed:
            raise ValueError(f"分类必须是以下之一: {allowed}")
        return v


class NewsSearchRequest(BaseModel):
    """自定义新闻搜索请求模型"""
    query: str = Field(..., min_length=1, max_length=100, description="搜索关键词")
    limit: int = Field(default=12, ge=1, le=30, description="返回数量")

    @field_validator("query")
    @classmethod
    def validate_query(cls, v):
        v = v.strip()
        if len(v) < 2:
            raise ValueError("搜索词太短（至少 2 字）")
        if re.search(r"<script|javascript:", v, re.IGNORECASE):
            raise ValueError("包含危险内容")
        return v


class NewsSummarizeRequest(BaseModel):
    """新闻 AI 摘要请求模型"""
    title: str = Field(..., min_length=1, max_length=300, description="新闻标题")
    summary: str = Field(default="", max_length=5000, description="已有正文/摘要（可选）")
    link: str = Field(default="", max_length=1000, description="原文链接（正文不足时兜底抓取）")

    @field_validator("title")
    @classmethod
    def validate_title(cls, v):
        if re.search(r"<script|javascript:", v, re.IGNORECASE):
            raise ValueError("包含危险内容")
        return v.strip()[:300]


class WriteRequest(BaseModel):
    """AI 写作请求（三模态：文字 + 图片 + 视频）"""
    topic: str = Field(..., min_length=1, max_length=500, description="核心思路/话题（必填）")
    news_ids: List[str] = Field(default=[], max_length=10, description="勾选的新闻素材 ID")
    upload_content: str = Field(default="", max_length=100000, description="上传参考文档内容")
    title: str = Field(default="", max_length=100, description="指定标题（留空 AI 拟）")
    with_images: bool = Field(default=True, description="是否生成配图")
    with_video: bool = Field(default=False, description="是否生成视频（慢且贵，默认关）")
    max_images: int = Field(default=4, ge=0, le=10, description="图片上限")
    max_videos: int = Field(default=1, ge=0, le=3, description="视频上限")
    skill_name: str = Field(default="wechat-writing", max_length=50)

    @field_validator("topic")
    @classmethod
    def validate_topic(cls, v):
        v = v.strip()
        if len(v) < 2:
            raise ValueError("话题太短（至少 2 字）")
        if re.search(r"<script|javascript:", v, re.IGNORECASE):
            raise ValueError("包含危险内容")
        return v
