# DraftBox AI 写作模块完整开发文档

> 状态: 已实施（2026-08-10，单元测试 48/48 + 后端/前端联调通过）
> 日期: 2026-08-10
> 适用代码库: draftbox_v2（Python/FastAPI 开源版）
> 设计依据: Go/VPS 版已验证的自进化 Skill 系统 + 三模态整合需求（文字/图片/视频）+ 无感自进化
>
> 实施记录与踩坑见 skill: `draftbox-backend-flutter` → `references/draftbox-v2-ai-writing-implementation.md`
> 待用户操作: `draftbox model` 配置 LLM key；方舟控制台开通更高质量 seedance/seedream 模型

---

## 1. 背景与目标

### 1.1 现状盘点（v2 开源版，本代码库）

| 模块 | 现状 | 说明 |
|------|------|------|
| 前端 AI写作 Tab | 占位符 | `web/src/App.jsx:190-199` 点击"生成"只设置提示文字，不调任何 API |
| 后端 AI 服务 | 不存在 | `backend/main.py` 只注册 news/convert/grammar/images/drafts/system/execute 七组路由 |
| Provider 系统 | 骨架 | `backend/providers/__init__.py` 有抽象基类 + Registry，零具体实现 |
| LLM 配置 | ✅ 已就绪 | `cli.py` 的 `draftbox model` 向导支持 34 个提供商，写入 `~/.draftbox/config.yaml` |
| 图片生成 | ✅ ARK 可用 | 火山方舟 Seedream 4.0 已实测开通（`doubao-seedream-4-0-250828`），详见 seedream-ark-image-api skill |
| 视频生成 | ✅ ARK 可用 | 火山方舟 Seedance 1.0 Pro 已实测开通（`doubao-seedance-1-0-pro-250528`） |
| Skill 系统 | 工具执行器 | `backend/tools/code_execution.py` 执行搬运的 hermes 工具型 skills，与写作进化无关 |
| 素材/排版/图片搜索 | ✅ 可用 | 热点新闻（VPS API + RSS 降级）、wewrite 排版转换、Pexels 搜索均正常 |

### 1.2 核心需求（2026-08-10 用户明确）

**AI 写作 = 文字 + 图片 + 视频 三模态整合，不是纯文字生成：**

1. **文字**：LLM 生成正文（原有能力）
2. **图片**：集成 OpenAI gpt-image-2 等图片生成模型；国产路径用火山方舟 Seedream（已有 key，实测可用）
3. **视频**：集成优质视频生成模型 API，生成适合文章叙事的短视频；国产路径用火山方舟 Seedance（已实测可用）
4. **整合**：三模态内容最终汇入一篇文章，排版可读性强，图片/视频在文中结构自然
5. **防泄露**：绝对不允许出现图片标签、HTML 代码等原始标记泄露到最终文章里

**作者真正关心的两件事（决定自进化方向）：**

- **排版是否规范、符合预期** → 自动质量门禁：每次生成后校验排版，违规自动修复，修复规则沉淀（无感）
- **内容是否垂直化、标签不混乱** → 垂直度校准：生成时输出标签，与账号垂直领域自动比对校准（无感）

**自进化机制（推翻手动 feedback）：**

- ❌ 手动提交 feedback 进化 → 不可取，不满足作者最简使用习惯（作者不会主动提交反馈）
- ✅ 无感自进化：进化信号全部来自作者的自然使用链路，零额外操作：
  - 学习目标自动学习（设置一次参考公众号，后台定时抓新文章自动学习）
  - 自动质量门禁（排版合规校验 + 修复规则沉淀）
  - 垂直度自动校准（标签领域比对 + 方向微调）
- ✅ 草稿不参与学习（已决策：草稿本身质量不稳定，学习信号不可靠）

### 1.3 VPS 版可移植的已验证资产（Go）

| 资产 | 说明 | 移植去向 |
|------|------|---------|
| 增量进化算法 | 去重检查 → 不存在才追加 → version+1 | skill_core/analyzer.py |
| Skill YAML 格式 | frontmatter + style/anti_patterns/positive_examples | skill_core/store.py |
| 8 维度风格分析 prompt | 标题/开头/段落/列表/引用/语气/数据/结尾 | analyzer.py（复用措辞） |
| stripMarkdownCodeBlock | LLM 返回 JSON 被 ``` 包裹的清洗 | utils（所有 LLM 调用先过） |
| 生成 prompt 优先级 | 思路 > 上传 > 新闻 > 风格 | builder.py |
| 锁教训 | LLM 调用不持锁（Go 死锁 Bug 59） | Python 用 asyncio.to_thread |
| news_ids 可空 | 素材允许为空（Bug 55） | writing.py 校验 |
| 本地爬虫代理 | 微信反爬（服务器 IP 必被封） | 可选 Task（URL 学习） |

---

## 2. 总体架构

### 2.1 三层架构

```
┌─────────────────────────────────────────────────────────────┐
│ 第三层 应用层 (draftbox 前端)                                  │
│  AI写作 Tab: 话题 + 新闻素材勾选 + 媒体开关(图片/视频)            │
│  → 生成(文字+图+视频) → 预览 → 转排版 → 保存草稿(带标签)          │
│  Skill 状态只在后端，前端不展示（用户明确要求）                    │
├─────────────────────────────────────────────────────────────┤
│ 第二层 适配层 (draftbox 后端 FastAPI)                          │
│  api/write.py     前端写作端点（生成 + 媒体 + 标签）             │
│  api/skill.py     内部 Skill 端点（current/learn/targets/log） │
│  service/writing.py  三模态编排（规划→媒体→整合→门禁）            │
│  service/skill_engine.py 无感进化引擎（目标学习/门禁沉淀/垂直度）  │
│  providers/chat.py    LLM Provider（mimo/deepseek/openai）    │
│  providers/image_gen.py  图片 Provider（seedream/gpt-image）   │
│  providers/video_gen.py  视频 Provider（seedance/可扩展）       │
├─────────────────────────────────────────────────────────────┤
│ 第一层 skill-core (独立开源核心库 evolve-write，纯 Python)       │
│  store.py      SkillStore: SKILL.md 读写/版本/日志             │
│  analyzer.py   SkillAnalyzer: 8维度风格提取 + 增量追加          │
│  gate.py       质量门禁: 排版合规校验 + 媒体完整性 + 防泄露       │
│  vertical.py   垂直度: 领域建模 + 标签校准                      │
│  builder.py    PromptBuilder: 三模态规划 prompt 组装           │
└─────────────────────────────────────────────────────────────┘
```

**分层原则：**
- skill-core 不 import fastapi/flask，只依赖 `requests` + `yaml` + 标准库 → 独立 pip 安装、单测、复用（开源仓库名已定：`evolve-write`）
- 适配层只做 HTTP 包装、配置读取、媒体下载缓存
- 应用层只做 UI 和状态，不碰算法

### 2.2 三模态写作管线（五阶段）

```
① 规划: LLM 生成正文 markdown，文中嵌入媒体占位符
        [IMG: 描述] → 图片位（AI 描述配图内容/场景/风格）
        [VID: 描述] → 视频位（AI 描述视频场景/时长/风格）
        同时输出 tags: [2-5 个标签]（垂直度）
   ↓
② 文字校验: 无未闭合占位符语法错误 → 修正
   ↓
③ 媒体生成:
   图片: 每个 [IMG:...] → ImageProvider → 下载到本地 → 替换占位符为 ![alt](本地URL)
   视频: 每个 [VID:...] → VideoProvider(异步任务轮询) → 下载 mp4 → 生成封面
         → 替换占位符为「视频卡片」标记（微信安全结构）
   ↓
④ 整合渲染: markdown → wewrite → HTML
   图片: 正常 <img>（微信兼容）
   视频: 卡片标记 → 样式化视频卡片 HTML（封面+播放按钮+说明+链接，无 <video> 标签）
   ↓
⑤ 质量门禁: 扫描最终 HTML
   - 无未替换的 [IMG:/[VID: 占位符残留
   - 无裸 <img>/<video>/<iframe>/javascript: 泄露
   - 媒体不打断段落结构（只出现在段间）
   - 标签垂直度比对（偏离 → 自动微调方向重生成一次）
   违规 → 自动修复（图片位用 Pexels 兜底图/视频位用文字卡片）或重生成
```

---

## 3. 数据模型

### 3.1 Writing Skill 文件格式（与 Hermes 兼容）

```
~/.draftbox/skills/wechat-writing/
├── SKILL.md
├── evolution.jsonl        # 进化日志（append-only，全部无感自动写入）
└── generations/           # 生成记录（含媒体清单，供复盘）
```

```yaml
---
name: wechat-writing
version: 12
use_count: 47
adopt_rate: 0.83          # 教训采纳率（防噪声进化）
vertical:                 # 账号垂直领域（从学习目标自动聚类）
  domain: 科技AI           # 领域名
  tags: [AI, 大模型, 创业, 效率工具]
  updated: 2026-08-10
created: 2026-08-01
updated: 2026-08-10
---

# 公众号文章写作规范

## style（8 维度风格，随学习进化）
### 开头
- ✅ 用一个具体场景/故事开头
- ❌ 不要用"最近XXX火了"

## structure
- 开头钩子 → 正文 2-3 小节 → 金句收尾

## media（媒体使用规范，随门禁沉淀）
### 图片
- ✅ 每 2-3 段插入一张配图，与段落内容强相关
- ✅ 配图描述含场景/构图/风格，利于生成模型出图
- ❌ 图片不能出现在标题后第一段（先文字后图）
### 视频
- ✅ 全文最多 1-2 个视频，插在关键场景处
- ✅ 视频描述 5-10 秒动态场景，适合文章叙事
- ❌ 视频不放开头（先建立阅读节奏）

## anti_patterns（作者明确不想要的）
- ❌ "XXX为何霸榜热搜"
- ❌ 泛泛而谈，没有具体案例

## positive_examples（作者改得好的片段）
### 样本 1：开头改写
- AI 初稿: "AI Agent 最近很火..."
- 作者终稿: "深夜的办公室，林遥的电脑弹窗跳出一行字..."
- 教训: 用具体场景代替抽象描述

## formatting（排版规范）
- 小标题用 ##，列表用 -，图片放段间
```

**8 维度风格**（analyzer 输出）：标题模式 / 开头风格 / 段落长度 / 列表风格 / 引用风格 / 语气风格 / 数据使用 / 结尾模式。

### 3.2 媒体缓存目录

```
~/.draftbox/media/
├── images/<draft_id>_<n>.png    # 生成图片（Seedream/gpt-image 产物）
├── videos/<draft_id>_<n>.mp4    # 生成视频（Seedance 产物）
└── covers/<draft_id>_<n>.jpg    # 视频封面（视频首帧/模型输出）
```

生成的文章中图片/视频用**本地相对路径引用**，由后端静态服务 `/media/` 提供（复用现有图片服务模式）；转排版时前端把本地路径替换为可访问 URL。

### 3.3 evolution.jsonl 格式（全部无感写入）

```json
{"version": 11, "type": "learn", "source": "https://mp.weixin.qq.com/s/xxx", "changes": ["style.opening: 用具体场景开头"], "ts": "2026-08-10T18:00:00"}
{"version": 12, "type": "gate", "issue": "html_leak", "fix": "裸img标签已降级为占位图", "lesson": "formatting: 媒体必须走占位符流程", "ts": "2026-08-10T18:05:00"}
{"version": 13, "type": "vertical", "drift": "tag: 娱乐 → 科技AI", "adjust": "重生成方向: 强化技术细节", "ts": "2026-08-10T18:10:00"}
```

### 3.4 配置结构（复用 cli.py + 新增媒体段）

```yaml
# ~/.draftbox/config.yaml
model:
  provider: mimo              # LLM: mimo / deepseek / openai
  model: mimo-v2.5-pro
  api_key: sk-xxx
  base_url: https://token-plan-cn.xiaomimimo.com/v1

image:
  provider: ark                # 图片: ark(seedream) / openai(gpt-image-2)
  model: doubao-seedream-4-0-250828
  api_key: e9af9ae7-...        # ARK key（用户已有）
  base_url: https://ark.cn-beijing.volces.com/api/v3

video:
  provider: ark                # 视频: ark(seedance) / 扩展: kling/veo/sora
  model: doubao-seedance-1-0-pro-250528
  api_key: e9af9ae7-...
  base_url: https://ark.cn-beijing.volces.com/api/v3
```

缺任一段配置 → 对应能力降级：无 `image` 段 → 图片用 Pexels 兜底；无 `video` 段 → 视频位渲染为"说明卡片"（不阻塞写作）。

---

## 4. API 契约

### 4.1 写作 API（前端使用）

**POST /api/write/generate** — 三模态生成

```json
// 请求
{
  "topic": "AI Agent 如何改变内容创作",        // 必填：核心思路/话题
  "news_ids": [1, 2, 3],                     // 可选：勾选的新闻素材 ID（第一版已支持勾选，上限10）
  "upload_content": "# 参考文档...",           // 可选：上传文件内容
  "title": "",                                // 可选：指定标题，留空 AI 拟
  "with_images": true,                        // 默认 true：生成配图
  "with_video": false,                        // 默认 false：视频较慢较贵，用户按需开
  "max_images": 4,                            // 图片上限（默认4）
  "max_videos": 1,                            // 视频上限（默认1）
  "skill_name": "wechat-writing"
}

// 响应 200（成功，含三模态结果）
{
  "success": true,
  "content": "## 正文 markdown（占位符已被替换为真实媒体引用）...",
  "html": "<style>...</style><div>渲染后的HTML...</div>",   // 直接可预览/复制
  "title": "AI Agent 正在重写内容生产的底层逻辑",
  "tags": ["AI", "大模型", "效率工具"],          // 垂直度标签
  "vertical_check": {"domain": "科技AI", "drifted": false, "note": "与账号领域一致"},
  "media": {
    "images": [{"idx": 1, "path": "/media/images/gen_x_1.png", "alt": "AI 办公场景配图"}],
    "videos": [{"idx": 1, "path": "/media/videos/gen_x_1.mp4", "cover": "/media/covers/gen_x_1.jpg", "caption": "AI 生成的演示视频"}]
  },
  "skill_version": 12,
  "draft_id": "gen_20260810_183000"
}

// 失败（未配置 LLM 模型）
// 200 + {"success": false, "error": "请先运行 draftbox model 配置模型"}
// 失败（topic 为空）
// 200 + {"success": false, "error": "请提供核心思路/话题"}
```

**POST /api/write/regenerate-media** — 只重生成媒体（图片/视频不满意时）

```json
// 请求
{"draft_id": "gen_xxx", "media_type": "image|video", "idx": 1, "prompt_override": "可选：覆盖原描述"}
// 响应: 同 generate 的 media 结构 + 更新后的 html
```

### 4.2 Skill 内部 API（后端内部/前端隐藏）

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/skill/current` | GET | 当前 Skill（YAML + version + vertical） |
| `/api/skill/targets` | GET/POST | 学习目标管理（参考公众号列表：名称+权重+抓取频率） |
| `/api/skill/learn` | POST | 手动提交参考文章（含 URL/文本/图片） |
| `/api/skill/evolution` | GET | 进化日志（learn/gate/vertical 三类） |
| `/api/skill/generations` | GET | 生成记录列表 |

### 4.3 错误处理规范

- 一律 HTTP 200 + `{"success": false, "error": "中文可读错误"}`（前端无异常分支）
- LLM 超时（120s）→ "模型响应超时，请重试"
- 图片/视频生成失败 → 不阻塞整体：图片位降级为 Pexels 兜底图，视频位降级为文字卡片，响应中 `media.warnings` 列出降级项
- LLM 返回非法 JSON → stripMarkdownCodeBlock 后仍失败 → 返回原始文本 + 提示
- 写操作幂等：learn 重复提交同一 source → "已学习过"，不重复进化

---

## 5. 核心算法

### 5.1 规划阶段（builder.py，三模态核心）

生成 prompt（含媒体规划指令）：

```
你是公众号写作专家。严格遵循以下写作规范（作者长期反馈沉淀的风格）：

{skill_yaml}

【作者核心思路，必须严格围绕】
{topic}

【新闻素材，可引用其中的事实和数据】
{news_items}

请写一篇公众号文章，要求：
1. 输出 Markdown，## 分节，800-1500 字
2. 标题另起一行以 # 开头
3. 在文中合适位置插入媒体占位符（不插入任何真实图片/视频代码）：
   - [IMG: 配图描述] —— 描述配图内容、场景、构图、风格，每 2-3 段一个，最多 {max_images} 个
   - [VID: 视频描述] —— 描述 5-10 秒动态场景，适合文章叙事，最多 {max_videos} 个（仅当需要时）
4. 占位符只能出现在段落之间，不能出现在标题行内或段落中间
5. 严格遵守写作规范中的 style/anti_patterns
6. 全文结尾输出标签行：标签: 标签1, 标签2, 标签3（2-5 个，与内容垂直度强相关）
```

**后处理（writing.py）：**
- stripMarkdownCodeBlock
- 提取标题（首行 `# xxx`）、提取标签行（`标签: xxx`），从正文剥离
- 校验占位符语法：`[IMG:` 必须闭合 `]`；统计图片/视频数量不超上限；超限截断
- 记录 draft_id，生成记录写入 `generations/`

### 5.2 媒体生成阶段

**图片（providers/image_gen.py）：**

```python
class ARKSeedreamProvider(ImageProvider):
    """火山方舟 Seedream —— 已验证格式（seedream-ark-image-api skill）"""
    def generate(self, prompt: str, size: str = "1920x1080") -> bytes:
        # POST {base_url}/images/generations
        # payload: {"model": "doubao-seedream-4-0-250828", "prompt": prompt,
        #           "size": "1920x1080",  # 🔴 横版必须显式写宽x高
        #           "response_format": "url", "watermark": False}
        # → data[0].url（TOS 签名 URL 1 天过期，立即下载）→ 返回 bytes
        # ⚠️ 不传 output_format 参数（400 坑）
        # ⚠️ 横版写 "1920x1080"，写 "2K" 会得到竖版（坑）

class OpenAIImageProvider(ImageProvider):
    """OpenAI gpt-image-2（可选，用户配置 OpenAI key 时启用）"""
    def generate(self, prompt: str, size: str = "1920x1080") -> bytes:
        # POST https://api.openai.com/v1/images/generations
        # payload: {"model": "gpt-image-2", "prompt": prompt, "size": "1920x1080",
        #           "n": 1, "response_format": "b64_json"}
        # → data[0].b64_json → bytes
```

每张图片：AI 描述的 `[IMG: 描述]` 直接作为 prompt 前缀 + 风格后缀（从 skill.media 沉淀），同步生成（~6 秒/张），**逐张串行**（避免限流），下载到 `~/.draftbox/media/images/`，占位符替换为 `![alt](/media/images/xxx.png)`。

**视频（providers/video_gen.py）—— 异步任务模式（已验证端点）：**

```python
class ARKSeedanceProvider(VideoProvider):
    """火山方舟 Seedance —— 异步任务 + 轮询"""
    def generate(self, prompt: str, duration: int = 5) -> dict:
        # 1. 创建任务: POST {base_url}/contents/generations/tasks
        #    payload: {"model": "doubao-seedance-1-0-pro-250528",
        #              "content": [{"type": "text", "text": prompt}],
        #              "duration": duration}
        #    → task.id
        # 2. 轮询: GET {base_url}/contents/generations/tasks/{id}（间隔 5s，上限 5 分钟）
        #    → status: queued/processing/succeeded/failed
        # 3. succeeded → content.video_url 下载 mp4；同时取封面（首帧或模型输出）
```

视频生成慢（1-5 分钟），**不阻塞主流程**：writing.py 先生成文字+图片返回给用户，视频任务后台继续；`/api/write/media-status?draft_id=xxx` 轮询视频状态，完成后自动整合进 HTML（前端轮询提示"视频生成中..."）。

**微信视频现实约束（必须遵守）：**
- 微信图文编辑器**不支持第三方 mp4 直接内嵌播放**（粘贴会被清洗）。只支持：图片直插、视频号/腾讯视频/本地视频（编辑器内上传）
- 因此 draftbox 生成的视频一律渲染为**视频卡片**（封面图 + 播放按钮 + 说明 + 链接），是纯图片+文字结构，微信 100% 兼容、不泄露任何 `<video>` 代码
- 作者可选择：a) 保留卡片（链接指向视频地址/视频号）；b) 在公众号编辑器用官方"视频"功能上传 mp4 替换

### 5.3 整合渲染阶段

**视频卡片标记**（markdown 层，防泄露的关键）：

```
@VIDEO_CARD(路径=/media/videos/gen_x_1.mp4, 封面=/media/covers/gen_x_1.jpg, 说明=AI 生成的演示视频, 链接=)
```

wewrite 转换后处理（convert 服务里加一道渲染）：`@VIDEO_CARD(...)` → 卡片 HTML：

```html
<figure style="margin:16px 0;text-align:center;">
  <a href="{链接或视频路径}" target="_blank" style="display:block;position:relative;border-radius:8px;overflow:hidden;">
    <img src="{封面}" style="width:100%;border-radius:8px;" alt="视频封面"/>
    <span style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:56px;height:56px;border-radius:50%;background:rgba(0,0,0,0.6);display:flex;align-items:center;justify-content:center;font-size:24px;color:#fff;">▶</span>
  </a>
  <figcaption style="color:#888;font-size:14px;margin-top:8px;">{说明}</figcaption>
</figure>
```

全部 inline style（微信清洗安全），无 `<video>`/`<iframe>` 标签。

### 5.4 质量门禁（gate.py，无感自进化核心之一）

生成完成后自动扫描最终 HTML：

```
GATE_CHECKS = [
  ("占位符残留",   r"\[(IMG|VID):",           "降级: 图片位用Pexels兜底图/视频位用文字卡片"),
  ("裸媒体标签",   r"<(video|iframe|embed)\b", "降级: 视频位改为说明卡片"),
  ("图片缺src",    r"<img(?!\s*src=)",         "修复: 补兜底图"),
  ("危险脚本",     r"javascript:|on\w+\s*=",   "移除: 危险属性"),
  ("段中媒体",     r"</p>\s*<img|<img[^>]*>\s*</p>",  "结构OK检查"),
]

def run_gate(html: str) -> GateResult:
    # 逐项扫描 → 命中则按 fix 策略降级/修复
    # 记录 issue/fix/lesson → 沉淀到 skill.formatting 或 skill.media（增量追加）
    # 有修复 → skill.version+1，写 evolution.jsonl type=gate
```

**门禁教训自动沉淀**（无感进化）：每次门禁修复，把"问题 → 修复方式"提炼为一条 formatting/media 规则增量追加进 skill。随着使用，排版问题出现频率递减——这就是"排版自进化"。

### 5.5 垂直度校准（vertical.py，无感自进化核心之二）

```
1. 领域建模（后台自动）:
   从学习目标公众号的近期文章标题/分类聚类（LLM 总结）
   → skill.vertical = {domain, tags}，每周自动更新
2. 生成时校准:
   规划阶段输出的 tags → 与 skill.vertical.tags 语义比对（LLM 判断）
   → 一致: 通过，返回 vertical_check.drifted=false
   → 偏离: 记录 drift → 自动调整（如 tag 娱乐 → 科技AI）
     重生成方向提示"强化技术细节，弱化娱乐表述" → 返回 drifted=true + 已修正
3. 沉淀: drift 记录写 evolution.jsonl type=vertical
```

标签同时随草稿保存（drafts API 加 tags 字段），前端草稿列表可按标签筛选（轻量）。

### 5.6 无感进化引擎（service/skill_engine.py）

**进化信号全部来自作者自然使用链路，零操作：**

| 信号 | 触发 | 沉淀 | 频率 |
|------|------|------|------|
| 目标学习 | 后台定时抓取 targets 中的公众号新文章 | analyzer 增量追加 style/anti_patterns | 每天/每公众号 |
| 门禁修复 | 每次生成后的质量门禁 | formatting/media 规则 | 每次生成 |
| 垂直度漂移 | 生成标签与领域偏离 | vertical 校准记录 | 每次生成 |

**增量追加算法（照搬 Go 版，防内容丢失）：**

```python
def apply_analysis(skill, analysis: dict) -> list:
    changes = []
    yaml_text = skill.raw_text
    for tech in analysis.get("techniques", []):
        if tech and tech not in yaml_text:      # 全文包含检查 → 去重
            yaml_text += f"\n- {tech}"
            changes.append(tech)
    for anti in analysis.get("anti_patterns", []):
        if anti and anti not in yaml_text:
            yaml_text += f"\n- ❌ {anti}"
            changes.append(f"anti: {anti}")
    for dim, val in analysis.get("style", {}).items():
        if val:
            yaml_text = upsert_style_dimension(yaml_text, dim, val)  # 同维度覆盖
            changes.append(f"style.{dim}: {val}")
    skill.raw_text = yaml_text
    return changes   # 空 → 不 bump version
```

**LLM 调用规范（全模块统一）：**
1. `strip_markdown_code_block(s)`：去 ``` 包裹，提取首 `{` 到末 `}` —— 所有 LLM 返回先过
2. 超时 120s，网络错误重试 1 次，业务错误不重试
3. 不持锁调 LLM：`asyncio.to_thread` 或每请求独立对象
4. key 缺失 → 立刻可读报错，不空转

---

## 6. 实现步骤（按序执行，每步一次写完整）

> 实施原则：一次性完整实现（用户偏好，杜绝迭代修 bug 循环），每 Task 完成即验证。

### Task 1: 三套 Provider 实现

**Files:**
- Create: `backend/providers/chat.py`（MimoProvider + DeepSeekProvider + OpenAIChatProvider，OpenAI 兼容格式）
- Create: `backend/providers/image_gen.py`（ARKSeedreamProvider + OpenAIImageProvider，见 5.2）
- Create: `backend/providers/video_gen.py`（ARKSeedanceProvider 异步任务轮询，见 5.2）
- Modify: `backend/providers/__init__.py`（`init_registry(config)` 按配置段注册三套）
- Modify: `backend/main.py`（启动时 init_registry）

**Step 1: 测试** `tests/test_providers.py`：配置注册、缺配置报错、seedream 请求体构造（mock requests）、seedance 任务轮询状态机（mock）。

**Step 2: 实现** 按 5.2 的已验证格式。图片/视频请求体必须带 `--noproxy` 语义（国内直连不走代理——requests 里 `trust_env=False` 或环境处理，避免 Clash 干扰本地服务）。

**Step 3: 验证**
```bash
cd backend && python -m pytest tests/test_providers.py -v
# 实网冒烟（用户 key 已开通模型）:
python -c "from providers.image_gen import ARKSeedreamProvider; print(len(ARKSeedreamProvider({'api_key':'e9af...','base_url':'https://ark.cn-beijing.volces.com/api/v3'}).generate('一只猫在键盘上', '1024x1024')))"
# 预期: 返回图片 bytes 长度 > 0
```

### Task 2: skill-core 基础（store.py）

**Files:**
- Create: `backend/skill_core/__init__.py`
- Create: `backend/skill_core/store.py`

**要点：** `SkillStore(base_dir=~/.draftbox/skills)`：load（frontmatter 解析）/save（原子写 tmp+rename）/bump_version/append_evolution（jsonl）/vertical 读写/media 记录。

**验证**：`python -m pytest tests/test_store.py`（读写/原子/版本/日志 5 用例）。

### Task 3: 规划 + 文字生成（builder.py + writing.py + api/write.py）

**Files:**
- Create: `backend/skill_core/builder.py`（5.1 的规划 prompt 组装）
- Create: `backend/service/writing.py`（generate_article 编排：规划→文字→门禁→标签）
- Create: `backend/api/write.py`（POST /api/write/generate）
- Modify: `backend/model/schemas.py`（WriteRequest/GenerateResponse Pydantic）
- Modify: `backend/main.py`（注册 write router）

**编排：**
```python
def generate_article(req):
    if not req.topic:
        return {"success": False, "error": "请提供核心思路/话题"}
    skill = store.load(req.skill_name) or DEFAULT_SKILL
    news_items = fetch_news_by_ids(req.news_ids)          # 复用 service/news.py
    prompt = builder.build_plan_prompt(skill, req, news_items)
    raw = llm_chat(prompt)                                 # 120s 超时，不持锁
    parsed = parse_article(raw)                            # 标题/正文/占位符/标签提取
    if not parsed["ok"]:
        return {"success": False, "error": "生成格式异常，请重试"}
    markdown = parsed["content"]
    if req.with_images:
        markdown = generate_images(markdown, req.max_images)   # 5.2 图片流程
    # 视频: 后台任务（见 Task 5），文字+图片先返回
    html = render_to_html(markdown)                        # wewrite + 视频卡片渲染
    gate = run_gate(html)                                  # 5.4 门禁
    vertical = check_vertical(parsed["tags"], skill)       # 5.5 垂直度
    save_generation(draft_id, markdown, html, media, tags)
    return {"success": True, ...}
```

**验证**：`python -m pytest tests/test_writing.py`（topic 校验/占位符解析/标签提取/门禁触发）；手动 curl 生成一篇纯文字+图片文章。

### Task 4: 前端 AI 写作 Tab（含新闻素材勾选 + 媒体开关）

**Files:**
- Modify: `web/src/App.jsx`（AI 写作区重写）
- Modify: `web/src/style.css`

**UI 布局（第一版即含新闻素材勾选，已决策）：**
```
[话题/核心思路输入框]                    [生成按钮]
[⚙ 媒体选项] ☑生成配图(默认)  ☐生成视频(默认关)
[新闻素材勾选区]
   ├─ 顶部: 分类选择（复用热点新闻分类数据，默认 TECH）
   ├─ 中部: 新闻列表（复用 /api/news/list，每项复选框：标题+来源+日期）
   └─ 底部: 已选 N 条 [清空]
[生成结果区]
   ├─ 标签条: #AI #大模型（垂直度提示: 与账号领域一致/已校准）
   ├─ markdown 预览（图片正常显示、视频卡片显示）
   └─ 按钮: [转为排版]→setMarkdown()切convert Tab / [保存草稿]→/api/drafts
```

**交互细节：**
- `selectedNews: Set<id>` 跨分类不清空，勾选上限 10 条，超出提示
- 生成期间 loading + 禁用；视频开启时轮询 `/api/write/media-status` 提示"视频生成中..."
- 生成结果 html 直接用（后端已渲染好），转排版时 setMarkdown(markdown)

**验证**：`cd web && cmd /c npm run build` 无错误；浏览器全流程点通。

### Task 5: 视频生成后台任务

**Files:**
- Modify: `backend/service/writing.py`（+generate_videos_background / media_status）
- Create: `backend/api/write.py` 加 `GET /api/write/media-status?draft_id=xxx`
- Create: `backend/service/media_task.py`（后台任务队列：asyncio.Task 或线程，任务状态持久化 JSON）

**要点：** 视频生成 1-5 分钟，任务独立于请求生命周期；完成后替换占位符、渲染卡片、更新 html 与 generations 记录；前端轮询 5s/次。

**验证**：mock seedance 返回 succeeded，验证任务状态流转 与 最终 html 含视频卡片且无 `<video>` 标签。

### Task 6: 整合渲染（wewrite 视频卡片 + 防泄露）

**Files:**
- Modify: `backend/service/convert.py`（convert_markdown 后处理：`@VIDEO_CARD(...)` 标记 → 卡片 HTML，见 5.3）
- Modify: `backend/model/schemas.py`（ConvertRequest 允许视频标记）

**验证**：`python -m pytest tests/test_convert.py`（视频卡片渲染、无裸标签、inline style 完整性）；转换输出粘贴模拟微信清洗后无代码残留。

### Task 7: 质量门禁 + 垂直度（gate.py + vertical.py）

**Files:**
- Create: `backend/skill_core/gate.py`（5.4 检查表 + 修复 + 教训沉淀）
- Create: `backend/skill_core/vertical.py`（5.5 领域建模 + 标签校准）
- Modify: `backend/service/skill_engine.py`（门禁/垂直度沉淀写 evolution.jsonl）

**验证**：`python -m pytest tests/test_gate.py` + `tests/test_vertical.py`（各 5 用例：残留占位符、裸标签、段中媒体、漂移检测、教训增量追加不重复）。

### Task 8: 无感进化（目标自动学习）

**Files:**
- Create: `backend/service/wechat_fetcher.py`（HTTP 多策略抓取，data-src 提取图片）
- Create: `backend/api/skill.py`（current/targets/learn/evolution/generations 端点）
- Modify: `backend/main.py`（注册 skill router + 后台定时任务：每日抓取 targets 新文章自动 learn）

**说明：** 微信反爬（服务器 IP 被封）→ fetch-url 失败时降级为本地爬虫代理（Task 9 可选）；targets 为空时不跑。

**验证**：配置一个 targets → 模拟定时触发 → skill version 递增、evolution 有 learn 记录；重复抓取同一篇不重复进化。

### Task 9: 本地爬虫代理（可选）

**Files:**
- Create: `crawler_proxy.py`（本地轮询 VPS 任务，WSL Chromium 抓取；模板见 skill `templates/crawler_proxy.py`）

**验证**：抓取一篇可公开访问的文章 URL 成功。

### Task 10: 整体联调 + 回归

**Files:**
- Modify: `README.md`（三模态 AI 写作使用说明：模型配置 + 媒体开关 + 垂直度）
- Modify: `cli.py`（可选：`draftbox skill list/current` 命令）

**验证清单（全过才算完成）：**
1. `python -m pytest tests/ -v` 全绿
2. `cd web && cmd /c npm run build` 成功
3. `cd backend && python -m uvicorn main:app --port 8502`；`curl --noproxy '*' http://127.0.0.1:8502/health` → ok
4. 前端全链路：话题 + 勾选新闻 + 开图片 → 生成 → 文章含图片（无 [IMG: 残留）→ 转排版 → 预览 → 保存草稿 → 草稿列表打开
5. 开视频 → 生成 → 轮询完成 → 文章含视频卡片（无 `<video>` 标签、无裸代码）→ 复制到公众号编辑器模拟验证
6. 生成 HTML 通过 gate 全项检查；日志有 gate/vertical 进化记录
7. targets 配置后自动学习生效，重复文章不重复进化
8. 未配置 model 时生成 → 可读错误；未配置 image 时图片位 Pexels 兜底

---

## 7. 测试策略

| 层 | 测试文件 | 覆盖 |
|----|---------|------|
| providers | `tests/test_providers.py` | 三套注册/缺配置/seedream 请求体/seedance 轮询状态机 |
| store | `tests/test_store.py` | 读写/原子/版本/日志/vertical |
| writing | `tests/test_writing.py` | topic 校验/占位符解析/标签提取/媒体编排 |
| convert | `tests/test_convert.py` | 视频卡片渲染/无裸标签/inline style |
| gate | `tests/test_gate.py` | 5 类检查项/降级修复/教训沉淀 |
| vertical | `tests/test_vertical.py` | 领域建模/漂移检测/校准 |
| 前端 | 手动 | 全链路回归（清单见 Task 10） |

**mock 策略：** LLM/图片/视频调用全部 monkeypatch 固定返回，不真调 API；实网冒烟单独脚本（Task 1 Step 3）。

---

## 8. 风险与开放问题

| # | 风险 | 应对 |
|---|------|------|
| 1 | 未配置 LLM 模型，写作不可用 | 可读错误 + README 指引 `draftbox model` |
| 2 | 未配置 image/video key | 图片位 Pexels 兜底、视频位文字卡片，不阻塞写作 |
| 3 | 视频生成慢（1-5 分钟） | 后台任务 + 前端轮询，文字+图片先交付 |
| 4 | 视频生成贵 | 默认关闭 with_video，用户按需开；max_videos 上限 1 |
| 5 | 微信不兼容第三方视频 | 视频卡片方案（纯图片+文字结构，见 5.3），提示作者可用公众号原生视频替换 |
| 6 | 单次噪声污染风格 | adopt_rate + 增量去重 + deprecated 机制 |
| 7 | 微信反爬抓不到参考文章 | 本地爬虫代理（Task 9）+ 手动粘贴 learn 降级 |
| 8 | LLM 输出格式不稳定 | stripMarkdownCodeBlock + 解析失败保留原文提示 |
| 9 | ARK 模型未开通（seedance-2.x/seedream-5.0 实测 404） | 默认用已开通的 seedream-4-0 / seedance-1-0-pro；文档注明开通路径（方舟控制台） |
| 10 | 多用户并发写同一 SKILL.md | 进程内锁 + 原子写（tmp+rename）；单机部署足够 |
| 11 | skill-core 开源后与 hermes skill 兼容 | 同格式，导出即可互相导入；后续加 `draftbox skill export/import` |
| 12 | 垂直度判断错误（误判漂移） | 校准只在"明确偏离"时触发（LLM 双确认），且只记录不强制重写（返回 drifted=true + 建议） |

**已决策事项（2026-08-10 用户确认）：**
1. ✅ 前端第一版即实现新闻素材勾选（上限 10 条，跨分类多选，topic 必填 + news_ids 可选）
2. ✅ skill-core 独立开源仓库命名 `evolve-write`
3. ✅ 草稿不参与学习（草稿质量不稳定，信号不可靠）
4. ✅ 不做手动 feedback 进化（不满足最简使用习惯）→ 改为无感进化（目标自动学习 + 门禁沉淀 + 垂直度校准）
5. ✅ AI 写作 = 文字 + 图片 + 视频三模态；图片默认开（gpt-image-2 可配 / Seedream 默认），视频默认关按需开
6. ✅ 作者关心的验收点：排版规范可预期、内容垂直化标签不混乱、图文视频交叉叙事、不泄露 HTML 代码

**开放问题（实施中确认即可）：**
1. 视频卡片链接指向哪？生成 mp4 本地路径（自托管预览）还是上传图床后公开 URL？（建议第一版：本地 /media/ 路径，README 说明作者可自行上传视频号后替换链接）
2. 垂直度领域是"每账号一个"还是"每目标公众号一个"？（建议第一版：每账号一个，从全部 targets 聚类）

---

## 附录 A：ARK 模型开通实测（2026-08-10，账号 2107487354）

| 模型 | 端点 | 状态 |
|------|------|------|
| `doubao-seedream-4-0-250828` | POST /api/v3/images/generations | ✅ 已开通可用 |
| `doubao-seedream-4-0-20260415` | POST /api/v3/images/generations | ✅ 已开通可用 |
| `doubao-seedream-5-0-260128` / `5-0-pro-260628` | 同上 | ❌ 404 需控制台开通 |
| `doubao-seedance-1-0-pro-250528` | POST /api/v3/contents/generations/tasks | ✅ 已开通可用（缺 content 报 400=已开通） |
| `doubao-seedance-1-0-pro-fast-251015` / `1-5-pro` / `2-0*` / `2-5` | 同上 | ❌ 404 需控制台开通 |

- 图片生成同步返回（~6 秒/张）；视频生成异步任务（创建 → 轮询 GET /contents/generations/tasks/{id}）
- 视频请求必填 `content: [{"type":"text","text":...}]` 参数（缺则 400 MissingParameter）
- 图片横版必须显式 `"size": "1920x1080"`；不传 `output_format`（400 坑）
- ARK 控制台开通路径：https://console.volcengine.com/ark → 开通管理 → 对应模型

## 附录 B：Go 版参考实现速查（移植对照）

| Go 文件 | Python 对应 | 说明 |
|---------|------------|------|
| `model/skill_types.go` | `backend/model/schemas.py` | 请求/响应结构 |
| `service/skill_engine.go` | `backend/skill_core/analyzer.py` + `service/skill_engine.py` | 进化引擎核心（增量追加） |
| `service/skill_storage.go` | `backend/skill_core/store.py` | 文件持久化 |
| `service/llm_client.go` | `backend/providers/chat.py` | LLM 调用（多模态） |
| `service/wechat_fetcher.go` | `backend/service/wechat_fetcher.py` | 公众号抓取（data-src） |
| `handler/skill.go` | `backend/api/skill.py` | API Handler |
| `crawler_proxy.go` | `crawler_proxy.py` | 本地爬虫代理（可选） |

## 附录 C：目录结构总览（实施完成后）

```
draftbox_v2/
├── backend/
│   ├── main.py                    # +write +skill 路由 + 定时任务
│   ├── api/
│   │   ├── write.py               # 新增：generate / regenerate-media / media-status
│   │   └── skill.py               # 新增：current/targets/learn/evolution/generations
│   ├── service/
│   │   ├── writing.py             # 新增：三模态编排
│   │   ├── skill_engine.py        # 新增：无感进化引擎
│   │   ├── media_task.py          # 新增：视频后台任务
│   │   └── wechat_fetcher.py      # 新增：公众号抓取
│   ├── providers/
│   │   ├── __init__.py            # +init_registry（三套注册）
│   │   ├── chat.py                # 新增：LLM（mimo/deepseek/openai）
│   │   ├── image_gen.py           # 新增：图片（seedream/gpt-image-2）
│   │   └── video_gen.py           # 新增：视频（seedance）
│   ├── skill_core/                # 新增（开源核心库 evolve-write）
│   │   ├── __init__.py
│   │   ├── store.py
│   │   ├── analyzer.py
│   │   ├── gate.py
│   │   ├── vertical.py
│   │   └── builder.py
│   └── model/schemas.py           # +WriteRequest/GenerateResponse
├── web/src/App.jsx                # AI 写作 Tab 重写（勾选+媒体+标签）
├── tests/                         # 新增：单元测试
└── crawler_proxy.py               # 新增（Task 9 可选）
```
