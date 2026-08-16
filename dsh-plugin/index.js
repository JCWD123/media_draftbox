/**
 * dsh-draftbox — DeepSeek Harness 插件
 * -------------------------------------
 * 把 media_draftbox（C:\...\draftbox_v2）的核心能力桥接为 Harness agent
 * 可调用的工具：
 *   draftbox_write_article   三模态写作（文字 + Seedream 配图 + Seedance 视频）
 *   draftbox_typeset         Markdown → 微信兼容内联样式 HTML
 *   draftbox_save_draft      保存草稿
 *   draftbox_list_drafts     列出草稿
 *   draftbox_get_draft       读取单篇草稿
 *   draftbox_illustrate      依据「发布物料.md」给文章 HTML 配图
 *   draftbox_search_images   Pexels 图片搜索
 *   draftbox_video_status    视频后台任务状态轮询
 *
 * 通过 HTTP 桥接到 mockbox 的 FastAPI 后端（默认 http://127.0.0.1:8502，
 * 可在 cordis.patch.yml 的 config.baseUrl 中覆盖）。
 *
 * 采用纯 ESM（无构建步骤），仅依赖 Harness 内置包：
 *   @deepseek-ai/dsh-tools  -> defineTool
 *   @deepseek-ai/cordis     -> Context 类型
 */
import { defineTool } from '@deepseek-ai/dsh-tools'

export const name = 'dsh-draftbox'
export const inject = ['tools']

const DEFAULTS = {
  baseUrl: 'http://127.0.0.1:8502',
  timeoutMs: 180000, // 写作/配图可能较久
}

// ---------------------------------------------------------------------------
// HTTP 细节
// ---------------------------------------------------------------------------

async function request(baseUrl, method, path, body, timeoutMs) {
  const ctrl = new AbortController()
  const timer = setTimeout(() => ctrl.abort(), timeoutMs)
  let resp
  try {
    resp = await fetch(`${baseUrl}${path}`, {
      method,
      signal: ctrl.signal,
      headers: body === undefined ? undefined : { 'content-type': 'application/json' },
      body: body === undefined ? undefined : JSON.stringify(body),
    })
  } catch (err) {
    throw new Error(`连接 media_draftbox 失败（${baseUrl}${path}）: ${err.message}`)
  } finally {
    clearTimeout(timer)
  }
  let data
  try {
    data = await resp.json()
  } catch {
    data = null
  }
  if (!resp.ok) {
    const detail = data && (data.detail || data.error) ? (data.detail || data.error) : resp.statusText
    throw new Error(`media_draftbox 返回 ${resp.status}: ${detail}`)
  }
  return data
}

// 把媒体相对路径补成可访问 URL，方便 agent 把配图直接交给用户/浏览器。
function absoluteMedia(baseUrl, html) {
  if (!html) return html
  return html.replaceAll('/media/', `${baseUrl}/media/`)
}

// ---------------------------------------------------------------------------
// 工具注册
// ---------------------------------------------------------------------------

export function apply(ctx, config) {
  const baseUrl = (config && config.baseUrl) || DEFAULTS.baseUrl
  const timeoutMs = (config && config.timeoutMs) || DEFAULTS.timeoutMs

  ctx.tools.register(defineTool({
    name: 'draftbox_write_article',
    description:
      '生成一篇完整的公众号草稿：给定核心思路/话题（可选勾选热点新闻素材、上传参考文档、指定标题），' +
      '让 media_draftbox 走「规划→文字→配图(Seedream/Pexels 兜底)→排版→质量门禁→垂直度」全流程，' +
      '输出 Markdown 源文 + 微信兼容的内联样式 HTML。可开启图片与（较慢较贵的）视频。',
    parameters: {
      topic: { type: 'string', required: true, description: '核心思路/话题（至少 2 字）' },
      news_ids: { type: 'array', items: { type: 'string' }, description: '已勾选的新闻素材 ID（来自 draftbox 热点新闻，最多 10 条）' },
      upload_content: { type: 'string', description: '上传参考文档/资料的文本内容' },
      title: { type: 'string', description: '指定标题（留空由 AI 拟定）' },
      with_images: { type: 'boolean', description: '是否生成配图（默认 true）' },
      with_video: { type: 'boolean', description: '是否生成视频（慢且贵，默认 false）' },
      max_images: { type: 'number', description: '图片上限 0-10（默认 4）' },
      max_videos: { type: 'number', description: '视频上限 0-3（默认 1）' },
      skill_name: { type: 'string', description: '写作 Skill（默认 wechat-writing）' },
    },
    output: {
      schema: {
        type: 'object',
        properties: {
          success: { type: 'boolean' },
          title: { type: 'string' },
          content: { type: 'string' },
          html: { type: 'string' },
          tags: { type: 'array', items: { type: 'string' } },
          video_pending: { type: 'boolean' },
          warnings: { type: 'array', items: { type: 'string' } },
        },
      },
      render: (_args, value) => {
        if (!value || value.success === false) {
          return [{ type: 'text', text: value && value.error ? value.error : '写作失败：未知错误' }]
        }
        const lines = [
          `✅ 已生成：《${value.title}》`,
          value.tags && value.tags.length ? `标签：${value.tags.join('、')}` : '标签：无',
          value.video_pending ? '⏳ 视频仍在后台生成中，请用 draftbox_video_status 查询 draft_id 状态。' : '',
          value.warnings && value.warnings.length ? `⚠️ 警告：\n${value.warnings.join('\n')}` : '',
          `\n--- Markdown 正文 ---\n${(value.content || '').slice(0, 4000)}`,
        ].filter(Boolean)
        return [{ type: 'text', text: lines.join('\n') }]
      },
    },
    async execute(args) {
      const result = await request(baseUrl, 'POST', '/api/write/generate', {
        topic: args.topic,
        news_ids: args.news_ids || [],
        upload_content: args.upload_content || '',
        title: args.title || '',
        with_images: args.with_images !== false,
        with_video: !!args.with_video,
        max_images: args.max_images !== undefined ? args.max_images : 4,
        max_videos: args.max_videos !== undefined ? args.max_videos : 1,
        skill_name: args.skill_name || 'wechat-writing',
      }, timeoutMs)
      if (result && result.html) {
        result.html = absoluteMedia(baseUrl, result.html)
      }
      return result
    },
  }))

  ctx.tools.register(defineTool({
    name: 'draftbox_typeset',
    description:
      '把 Markdown 排版为「可直接粘贴进公众号编辑器」的微信兼容内联样式 HTML。' +
      '20 种主题可选（professional-clean / premium / minimal / github / ink / midnight 等）。',
    parameters: {
      markdown: { type: 'string', required: true, description: 'Markdown 源文' },
      theme: { type: 'string', description: '排版主题（默认 professional-clean）。可用：premium, professional, minimal, github, newspaper, bold-navy, professional-clean, bauhaus, bold-green, bytedance, elegant-rose, focus-red, impeccable, ink, lobster-notes, midnight, minimal-gold, sspai, tech-modern, warm-editorial' },
    },
    output: {
      schema: { type: 'object', properties: { html: { type: 'string' }, error: { type: 'string' } } },
      render: (_args, value) => {
        if (!value || value.error) return [{ type: 'text', text: value && value.error ? value.error : '排版失败' }]
        return [{ type: 'text', text: `已排版（HTML 约 ${value.html.length} 字符）。html 字段含完整内联样式，可直接粘贴到 mp.weixin.qq.com 编辑器。` }]
      },
    },
    async execute(args) {
      const result = await request(baseUrl, 'POST', '/api/convert', {
        markdown: args.markdown,
        theme: args.theme || 'professional-clean',
      }, 60000)
      if (result && result.html) result.html = absoluteMedia(baseUrl, result.html)
      return result
    },
  }))

  ctx.tools.register(defineTool({
    name: 'draftbox_save_draft',
    description: '把一篇内容保存进 media_draftbox 的草稿箱。可同时给 Markdown 源文与排版后的 HTML。',
    parameters: {
      title: { type: 'string', required: true, description: '草稿标题（最长 50 字，会过滤特殊字符）' },
      content: { type: 'string', required: true, description: 'Markdown 源内容' },
      html: { type: 'string', description: '排版后的 HTML（可选）' },
    },
    output: {
      schema: { type: 'object', properties: { ok: { type: 'boolean' }, filename: { type: 'string' }, title: { type: 'string' } } },
      render: (_args, value) => {
        if (!value || value.ok === false) return [{ type: 'text', text: '保存草稿失败' }]
        return [{ type: 'text', text: `已保存草稿《${_args.title}》 -> ${value.filename}` }]
      },
    },
    async execute(args) {
      const result = await request(baseUrl, 'POST', '/api/drafts', {
        title: args.title,
        content: args.content,
        html: args.html || '',
      }, 30000)
      return { ok: result.ok, filename: result.filename, title: args.title }
    },
  }))

  ctx.tools.register(defineTool({
    name: 'draftbox_list_drafts',
    description: '列出 media_draftbox 草稿箱中的所有草稿（标题 + 更新时间）。',
    parameters: {},
    output: {
      schema: { type: 'object', properties: { drafts: { type: 'array' } } },
      render: (_args, value) => {
        const drafts = (value && value.drafts) || []
        return [
          { type: 'text', text: drafts.length ? drafts.map((d) => `· ${d.title}  (${d.filename})  [${d.updated_at || ''}]`).join('\n') : '（草稿箱为空）' },
        ]
      },
    },
    async execute() {
      const result = await request(baseUrl, 'GET', '/api/drafts', undefined, 30000)
      return { drafts: (result && result.drafts) || [] }
    },
  }))

  ctx.tools.register(defineTool({
    name: 'draftbox_get_draft',
    description: '读取单篇草稿的完整内容（标题 / Markdown 源文 / 排版 HTML / 更新时间）。',
    parameters: {
      filename: { type: 'string', required: true, description: '草稿文件名（来自 draftbox_list_drafts 的 filename 字段）' },
    },
    output: {
      schema: {
        type: 'object',
        properties: {
          title: { type: 'string' },
          markdown: { type: 'string' },
          html: { type: 'string' },
          updated_at: { type: 'string' },
        },
      },
      render: (_args, value) => {
        if (!value) return [{ type: 'text', text: '草稿不存在' }]
        return [{ type: 'text', text: `《${value.title}》  (更新于 ${value.updated_at || '未知'})\n\n--- Markdown ---\n${(value.markdown || '(无 markdown)').slice(0, 3000)}` }]
      },
    },
    async execute(args) {
      const result = await request(baseUrl, 'GET', `/api/drafts/${encodeURIComponent(args.filename)}`, undefined, 30000)
      if (result && result.html) result.html = absoluteMedia(baseUrl, result.html)
      return result
    },
  }))

  ctx.tools.register(defineTool({
    name: 'draftbox_illustrate',
    description:
      '给一篇已经存在的文章 HTML 配图。输入文章 HTML 与「发布物料.md」内容，' +
      'media_draftbox 会解析物料里的配图锚点 + 英语配图提示词，调用 Seedream 生成并把图片插入文章末尾。',
    parameters: {
      html: { type: 'string', required: true, description: '文章 HTML（微信兼容）' },
      material_md: { type: 'string', required: true, description: '「发布物料.md」文本内容（含配图提示词）' },
    },
    output: {
      schema: {
        type: 'object',
        properties: {
          success: { type: 'boolean' },
          html: { type: 'string' },
          inserted: { type: 'number' },
          warnings: { type: 'array', items: { type: 'string' } },
        },
      },
      render: (_args, value) => {
        if (!value || value.success === false) {
          return [{ type: 'text', text: value && value.error ? value.error : '配图失败' }]
        }
        const lines = [`已配图 ${value.inserted ?? 0} 张。`, ...(value.warnings || []).map((w) => `⚠️ ${w}`)]
        return [{ type: 'text', text: lines.join('\n') }]
      },
    },
    async execute(args) {
      const result = await request(baseUrl, 'POST', '/api/illustrate', {
        html: args.html,
        material_md: args.material_md,
      }, timeoutMs)
      if (result && result.html) result.html = absoluteMedia(baseUrl, result.html)
      return result
    },
  }))

  ctx.tools.register(defineTool({
    name: 'draftbox_search_images',
    description: '用关键词在 Pexels 搜索真实图片（返回可外链的图片 URL 列表）。适用于文章配图选真实摄影图而非 AI 生成图的场景。',
    parameters: {
      query: { type: 'string', required: true, description: '搜索关键词（最多 100 字）' },
      count: { type: 'number', description: '返回数量 1-50（默认 12）' },
    },
    output: {
      schema: {
        type: 'object',
        properties: {
          images: {
            type: 'array',
            items: { type: 'object', properties: { url: { type: 'string' } } },
          },
        },
      },
      render: (_args, value) => {
        const imgs = (value && value.images) || []
        return [{ type: 'text', text: imgs.length ? imgs.map((i, idx) => `${idx + 1}. ${i.url}`).join('\n') : '（无结果）' }]
      },
    },
    async execute(args) {
      return request(baseUrl, 'POST', '/api/images/search', {
        query: args.query,
        count: args.count !== undefined ? args.count : 12,
      }, 30000)
    },
  }))

  ctx.tools.register(defineTool({
    name: 'draftbox_video_status',
    description: '查询某篇草稿的视频后台生成状态（draft_id 来自 draftbox_write_article 的返回）。',
    parameters: {
      draft_id: { type: 'string', required: true, description: '草稿/生成任务的 draft_id' },
    },
    output: {
      schema: {
        type: 'object',
        properties: {
          success: { type: 'boolean' },
          status: { type: 'string' },
          videos: { type: 'array' },
          html: { type: 'string' },
        },
      },
      render: (_args, value) => [{ type: 'text', text: `视频任务状态：${value.status}（draft_id=${_args.draft_id}）` }],
    },
    async execute(args) {
      const result = await request(baseUrl, 'GET', `/api/write/media-status?draft_id=${encodeURIComponent(args.draft_id)}`, undefined, 30000)
      if (result && result.html) result.html = absoluteMedia(baseUrl, result.html)
      return result
    },
  }))
}
