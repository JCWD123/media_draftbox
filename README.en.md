# DraftBox

> **🌏 Language / 语言: [English](README.en.md) | [简体中文](README.md)**

Self-learning AI writing assistant — full workflow for WeChat Official Account content

> **One-stop workflow: AI writing, news material, layout conversion, draft management. Supports cloud LLM (text + image + video) generation, 18+ layout themes, and custom news search.**

## ✨ Features

- **AI Writing**: Connect to OpenAI-compatible LLMs to generate Official Account articles in one click (text + images + videos)
- **News Material**: 7 real-time hot categories + custom keyword search; selectable as writing material; per-item AI summary
- **Layout Conversion**: Built-in 18+ wewrite themes, WeChat-compatible styles, one-click HTML copy
- **Draft Management**: AI-generated articles are auto-saved as drafts; review, re-layout, and copy anytime
- **Image Search**: Unsplash + Pexels
- **Model Config**: Multiple providers (hermes-style)

## 🎬 Video Demo

[▶️ Play demo video](docs/media/draftbox-demo.mp4)

> A full walkthrough of DraftBox: AI writing → news material → layout conversion → draft management.

<video controls width="100%">
  <source src="docs/media/draftbox-demo.mp4" type="video/mp4">
  Your browser does not support the video tag. Please download the video to view.
</video>

## 💬 Join the Community

Scan the QR code below to join the AI-writing discussion group:

![WeChat group QR](docs/media/wechat-group-qr.jpg)

## 📚 Showcase Examples (AI Writing Output)

These two articles were generated end-to-end with DraftBox AI Writing. Open `docs/examples/*.html` in a browser to view (includes images + WeChat layout):

| Example | Markdown | Layout HTML | Highlights |
|---------|----------|-------------|-----------|
| **3 scenarios: how OpenHarness makes AI assistants truly "useful"** | [openharness.md](docs/examples/openharness-3-scenarios.md) | [openharness.html](docs/examples/openharness-3-scenarios.html) | 4 AI-generated images, story-driven opening |
| **Stop making a marketing pitch out of the Fields Medal** | [fields.md](docs/examples/fields-medal-openai.md) | [fields.html](docs/examples/fields-medal-openai.html) | In-depth long-form, classic WeChat layout |

## 🚀 Installation

### Linux / macOS
```bash
curl -fsSL https://raw.githubusercontent.com/JCWD123/media_draftbox/main/install.sh | bash
```

### Windows PowerShell
```powershell
irm https://raw.githubusercontent.com/JCWD123/media_draftbox/main/install.ps1 | iex
```

## 🐳 Docker Deployment

> **Faster image pulls with Chinese mirrors**: pulling from official Docker Hub (docker.io) can be slow in China — use a Chinese mirror accelerator (e.g. `docker.m.daocloud.io`) for much faster speed.

### Build the image (with China mirror acceleration)

The project ships a `Dockerfile` that already uses **China apt / pip / npm mirrors** (Aliyun + npmmirror), much faster than the official sources:

```bash
# From the project root
docker build -t draftbox .
```

> To use a China mirror for the base image as well, replace the base image in the Dockerfile:
> ```dockerfile
> FROM docker.m.daocloud.io/library/python:3.11-slim
> ```

### Run

```bash
# Start (frontend 3000 + backend 8502)
docker run -d -p 3000:3000 -p 8502:8502 --name draftbox draftbox

# View logs
docker logs -f draftbox

# Stop / remove
docker stop draftbox && docker rm draftbox
```

### Configure the model key

AI writing needs an LLM key. Mount your local config into the container (recommended — keeps the key out of the image):

```bash
docker run -d -p 3000:3000 -p 8502:8502 \
  -v "$HOME/.draftbox/config.yaml:/root/.draftbox/config.yaml" \
  --name draftbox draftbox
```

Then visit http://localhost:3000 to use it. API docs are at http://localhost:8502/docs.

## 💻 Usage

```bash
# Start
draftbox

# Model config
draftbox model

# Setup wizard
draftbox setup
```

## 📂 Project Structure

```
docs/
├── examples/          # AI writing showcase examples (HTML + Markdown + images)
├── media/             # demo video, WeChat group QR
├── AI-WRITING-DEV.md  # AI writing dev docs
└── GITHUB_FLOW.md     # GitHub Flow spec
web/                   # React frontend
backend/               # FastAPI backend
```

## Repository

https://github.com/JCWD123/media_draftbox

## License

MIT
