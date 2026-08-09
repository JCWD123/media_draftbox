# DraftBox

会学习的 AI 写作助手 - 公众号内容全流程

## 核心特性

- **自进化 Skill**：内置后端，随创作风格持续进化
- **18+ 主题**：集成 wewrite 引擎
- **npm 包渲染**：markdown-it + highlight.js + katex + mermaid
- **配置管理**：交互式终端配置（参考 Hermes）

## 快速开始

```bash
# 1. 配置
python cli.py config init

# 2. 启动后端
cd backend && python -m uvicorn main:app --port 8502

# 3. 启动前端
cd web && npm install && npm run dev
```

## 配置文件

位置：`~/.draftbox/config.yaml`

```yaml
model:
  api_key: "your-api-key"
  base_url: "https://token-plan-cn.xiaomimimo.com/v1"
  model: "mimo-v2.5"

search:
  pexels_key: "your-pexels-key"

server:
  backend_port: 8502
  web_port: 3000
```

## CLI 命令

```bash
draftbox config init    # 交互式配置向导
draftbox config list    # 查看配置
draftbox config set     # 设置配置
draftbox config get     # 获取配置
```

## 项目结构

```
draftbox_v2/
├── backend/main.py      # FastAPI 后端
├── web/                 # React 前端
│   ├── src/App.jsx
│   └── package.json
├── src/wewrite/         # wewrite 引擎
├── cli.py               # CLI 配置工具
└── README.md
```

## 集成的开源项目

| 项目 | 功能 | 集成方式 |
|------|------|---------|
| wewrite | Markdown→微信HTML | npm 包 + CLI |
| doocs/md | Markdown渲染 | markdown-it |
| highlight.js | 代码高亮 | npm 包 |
| katex | 数学公式 | npm 包 |
| mermaid | 图表 | npm 包 |

## License

MIT
