# dsh-draftbox

DeepSeek Harness 插件：把 [media_draftbox](https://github.com/JCWD123/media_draftbox)（公众号文章草稿箱）的核心能力桥接为 Harness agent 可调用的工具。

media_draftbox 后端是 Python/FastAPI，负责「三模态 AI 写作」：文字（DeepSeek/MiMo）→ 配图（火山方舟 Seedream，Pexels 兜底）→ 视频（Seedance）→ 微信兼容排版 → 质量门禁 → 草稿管理。本插件把这些能力封装成工具，让 DeepSeek Harness 的 agent 能直接调用，实现「一句话让 agent 帮你写完一篇带图带排版的公众号稿子」。

> 插件采用纯 ESM（无构建步骤），仅依赖 Harness 内置的 `@deepseek-ai/dsh-tools` 与 `@deepseek-ai/cordis`。

## 快速开始

### 前置：先把 media_draftbox 后端跑起来

```sh
cd draftbox_v2/backend
uvicorn main:app --host 127.0.0.1 --port 8502 --reload
```

确保模型 / 图片 / 视频已通过 `draftbox model` 配置（见 media_draftbox 仓库 README）。

### 安装插件（两种方式）

**方式 A：本地 checkout（推荐开发）**

```sh
# 1. 安装插件自身的依赖（pnpm 会把 @deepseek-ai/dsh-tools / @deepseek-ai/cordis
#    装进 dsh-plugin/node_modules，`dsh plugin add` 以 link: 方式安装时需要它们）
cd dsh-plugin && pnpm install && cd ..

# 2. 装进 dsh 的 headless / 自定义 profile
dsh plugin --profile demo add ./dsh-plugin
```

**方式 B：从 GitHub 安装**

```sh
# 需要 Node ≥ 22.19（dsh 依赖较新运行时），且 dsh 已安装（npx @deepseek-ai/dsh 或 npm i -g @deepseek-ai/dsh）
dsh plugin --profile demo add github:JCWD123/media_draftbox
```

安装后启动：

```sh
dsh --profile demo
```

验证插件被加载：

```sh
dsh --profile demo --dump-config   # 应看到 "# == dsh-draftbox" 这一层
```

然后向 agent 下指令，例如：

> 帮我把「DeepSeek Harness 详解」写成一篇文章：先勾选几篇热点素材，正文配 4 张图，用 midnight 主题排版，最后存进草稿箱。

## 一键回归测试

装好 dsh + pnpm + npm（安装见上）后，一条命令跑通端到端自测：

```sh
cd dsh-plugin
bash test-e2e.sh              # 工具层自测：启动/复用后端 + list/get/save/typeset/search 真实断言（无 LLM 成本）
bash test-e2e.sh --with-agent # 额外用真实 dsh agent 调一次 draftbox_list_drafts（需 DEEPSEEK_API_KEY）
bash test-e2e.sh --keep-backend # 测试结束后不关闭它拉起的后端
```

- 退出码 `0`=全通过；`1`=有失败；`2`=前置缺失（node/pnpm/dsh）。
- 测试产生的草稿会自动清理；若脚本自己拉起了后端，默认会关闭它（`--keep-backend` 保留）。
- 纯工具层自测不调用 LLM：5 个常规工具做真实断言（list/get/save/typeset/search），3 个多模态工具
  （write_article/illustrate/video_status）做契约级断言（命中后端校验/错误分支，不真触发 LLM/Seedream/Seedance）。

## 提供的工具

| 工具 | 说明 | 对应后端 API |
|---|---|---|
| `draftbox_write_article` | 三模态写一整篇公众号稿（文字+配图+可选视频） | `POST /api/write/generate` |
| `draftbox_typeset` | Markdown → 微信兼容内联样式 HTML（20 主题） | `POST /api/convert` |
| `draftbox_save_draft` | 保存草稿（含排版 HTML） | `POST /api/drafts` |
| `draftbox_list_drafts` | 列出草稿箱 | `GET /api/drafts` |
| `draftbox_get_draft` | 读取单篇草稿 | `GET /api/drafts/{filename}` |
| `draftbox_illustrate` | 依据「发布物料.md」给文章 HTML 配图 | `POST /api/illustrate` |
| `draftbox_search_images` | Pexels 真实图片搜索 | `POST /api/images/search` |
| `draftbox_video_status` | 视频后台任务状态轮询 | `GET /api/write/media-status` |

## 配置

默认连 `http://127.0.0.1:8502`。若后端在 Docker / VPS，在 profile 的 `cordis.patch.yml` 覆盖 `baseUrl`：

```yaml
# 你的 profile：$DSH_HOME/profiles/<name>/cordis.patch.yml
- patch:
    - id: dsh-draftbox
      config:
        baseUrl: http://your-host:8502
```

| 键 | 默认 | 说明 |
|---|---|---|
| `baseUrl` | `http://127.0.0.1:8502` | media_draftbox 后端地址 |
| `timeoutMs` | `180000` | 单次请求超时（写作/配图较慢） |

## 模型能力边界

- 生成视频（`with_video: true`）较慢较贵，且走后台任务，完成后需用 `draftbox_video_status` 轮询 `draft_id`。
- 图片源：优先火山方舟 Seedream；图片服务欠费（`AccountOverdueError`）时自动降级 Pexels，仍有失败会进工具的 `warnings` 字段。
- `draftbox_get_draft` 里的 `html` 已把 `/media/` 相对路径改写为 `baseUrl` 绝对路径，方便直接访问生成的图片/视频。

## LICENSE

MIT。本插件归属 DeepSeek Harness 插件生态，仓库请打上 [`dsh-plugin`](https://github.com/topics/dsh-plugin) 话题便于被发现。
