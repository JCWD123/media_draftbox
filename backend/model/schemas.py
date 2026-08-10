"""
数据模型 - Pydantic 校验
防止 SQL 注入、XSS 攻击等安全问题
"""
from pydantic import BaseModel, Field, validator
from typing import Optional
import re


class ConvertRequest(BaseModel):
    """转换请求模型"""
    markdown: str = Field(..., min_length=1, max_length=100000, description="Markdown 内容")
    theme: str = Field(default="professional-clean", max_length=50)

    @validator("markdown")
    def validate_markdown(cls, v):
        # 过滤危险内容
        if re.search(r"<script|javascript:|on\w+\s*=", v, re.IGNORECASE):
            raise ValueError("包含危险内容")
        return v.strip()

    @validator("theme")
    def validate_theme(cls, v):
        allowed = ["professional", "minimal", "github", "newspaper", "bold-navy"]
        if v not in allowed:
            raise ValueError(f"主题必须是以下之一: {allowed}")
        return v


class DraftSaveRequest(BaseModel):
    """草稿保存请求模型"""
    title: str = Field(..., min_length=1, max_length=100, description="草稿标题")
    content: str = Field(..., min_length=1, max_length=500000, description="草稿内容")

    @validator("title")
    def validate_title(cls, v):
        # 过滤特殊字符
        v = re.sub(r'[<>:"/\\|?*]', "", v)
        return v.strip()[:50]

    @validator("content")
    def validate_content(cls, v):
        # 过滤危险内容
        if re.search(r"<script|javascript:", v, re.IGNORECASE):
            raise ValueError("包含危险内容")
        return v


class GrammarCheckRequest(BaseModel):
    """语法检查请求模型"""
    text: str = Field(..., min_length=1, max_length=10000, description="待检查文本")
    language: str = Field(default="zh", max_length=10)

    @validator("language")
    def validate_language(cls, v):
        allowed = ["zh", "en", "ja", "ko", "fr", "de", "es"]
        if v not in allowed:
            raise ValueError(f"语言必须是以下之一: {allowed}")
        return v


class ImageSearchRequest(BaseModel):
    """图片搜索请求模型"""
    query: str = Field(..., min_length=1, max_length=100, description="搜索关键词")
    count: int = Field(default=12, ge=1, le=50, description="返回数量")

    @validator("query")
    def validate_query(cls, v):
        # 过滤特殊字符
        v = re.sub(r'[<>:"/\\|?*]', "", v)
        return v.strip()


class NewsRequest(BaseModel):
    """新闻请求模型"""
    category: str = Field(default="TECH", max_length=20)
    page: int = Field(default=1, ge=1, le=100)
    page_size: int = Field(default=20, ge=1, le=100)

    @validator("category")
    def validate_category(cls, v):
        allowed = ["FINANCE", "TECH", "SOCIAL", "DEVELOPER", "VIDEO", "COMMUNITY", "KNOWLEDGE"]
        if v not in allowed:
            raise ValueError(f"分类必须是以下之一: {allowed}")
        return v
