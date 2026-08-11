# DraftBox

会学习的 AI 写作助手 - 公众号内容全流程

> **AI 写作、新闻素材、排版转换、草稿管理一站式工作流。支持云端大模型（文字 + 图片 + 视频）生成、18+ 排版主题、自定义新闻搜索。**

## ✨ 功能

- **AI 写作**：接入 OpenAI 兼容大模型，一键生成公众号文章（文字 + 配图 + 视频）
- **新闻素材**：7 大类实时热点 + 自定义关键词搜索，勾选后可作写作素材；每条支持 AI 摘要
- **排版转换**：集成 18+ wewrite 主题，公众号兼容样式，一键复制 HTML
- **草稿管理**：AI 写作完成后自动保存草稿，可随时回看、排版、复制
- **图片搜索**：Unsplash + Pexels
- **模型配置**：多提供商（类 hermes）

## 🎬 视频演示

[▶️ 点击播放演示视频](docs/media/draftbox-demo.mp4)

> 完整录制了 DraftBox 的 AI 写作 → 新闻素材 → 排版转换 → 草稿管理全流程。

<video controls width="100%">
  <source src="docs/media/draftbox-demo.mp4" type="video/mp4">
  您的浏览器不支持 video 标签，请下载视频查看。
</video>

## 💬 加入交流群

扫描下方二维码加入「学长十一」AI 写作交流群：

![微信群二维码](docs/media/wechat-group-qr.jpg)

## 📚 示范案例（AI 写作产出）

以下两个案例是使用 DraftBox AI 写作生成的完整公众号文章，可直接浏览器打开 `docs/examples/*.html` 查看（含配图 + 微信排版）：

| 案例 | Markdown | 排版 HTML | 亮点 |
|------|----------|-----------|------|
| **3个场景，告诉你 OpenHarness 如何让 AI 助理真正“有用”** | [openharness.md](docs/examples/openharness-3-scenarios.md) | [openharness.html](docs/examples/openharness-3-scenarios.html) | 含 4 张 AI 配图，故事化开头 |
| **别再拿菲尔兹奖营销了** | [fields.md](docs/examples/fields-medal-openai.md) | [fields.html](docs/examples/fields-medal-openai.html) | 深度长文，微信经典排版 |

### 案例一：OpenHarness 智能体（AI 写作 + 配图示例）

<details>
<summary>查看案例 HTML 预览</summary>

![案例配图](docs/examples/images/gen_20260811_224814_1.png)

[打开完整 HTML](docs/examples/openharness-3-scenarios.html)

</details>

## 🚀 安装

### Linux / macOS
```bash
curl -fsSL https://raw.githubusercontent.com/JCWD123/media_draftbox/main/install.sh | bash
```

### Windows PowerShell
```powershell
irm https://raw.githubusercontent.com/JCWD123/media_draftbox/main/install.ps1 | iex
```

## 💻 使用

```bash
# 启动
draftbox

# 模型配置
draftbox model

# 配置向导
draftbox setup
```

## 📂 目录结构

```
docs/
├── examples/          # AI 写作示范案例（HTML + Markdown + 配图）
├── media/             # 演示视频、微信群二维码
├── AI-WRITING-DEV.md  # AI 写作开发文档
└── GITHUB_FLOW.md     # GitHub Flow 规范
web/                   # React 前端
backend/               # FastAPI 后端
```

## 仓库

https://github.com/JCWD123/media_draftbox

## License

MIT
