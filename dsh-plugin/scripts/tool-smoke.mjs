#!/usr/bin/env node
/**
 * dsh-draftbox 工具层自测（无 LLM 依赖）。
 *
 * 加载插件的真实 index.js（连同插件自身的 node_modules 里的真实
 * @deepseek-ai/dsh-tools），对它暴露的 8 个工具做 HTTP 级断言：
 *   draftbox_list_drafts / get_draft / save_draft / typeset / search_images
 * 全部通过后端真实媒体验证。多模态/write_article/illustrate/video_status
 * 需要模型 key，这里只做参数契约校验（不真调 LLM/Seedream）。
 *
 * 用法：node scripts/tool-smoke.mjs [--base-url http://127.0.0.1:8502]
 * 退出码：0=全通过，1=有失败。测试产生的草稿会自动清理。
 */
import { fileURLToPath, pathToFileURL } from 'node:url'
import { dirname, join } from 'node:path'

const __dirname = dirname(fileURLToPath(import.meta.url))
const PLUGIN_INDEX = join(__dirname, '..', 'index.js')

// 解析 --base-url
const arg = process.argv.find((a) => a.startsWith('--base-url='))
const BASE_URL = arg ? arg.split('=')[1] : 'http://127.0.0.1:8502'

// 直接 import 插件真实 index.js；@deepseek-ai/dsh-tools 会从插件自己的
// node_modules（pnpm install 装好）原生解析，含 transitive 依赖。
let plugin
try {
  plugin = await import(pathToFileURL(PLUGIN_INDEX).href)
} catch (e) {
  console.error(`[ERROR] 加载插件失败: ${e.message}\n  请先运行: cd dsh-plugin && pnpm install`)
  process.exit(2)
}

const tools = []
plugin.apply({ tools: { register: (t) => tools.push(t) } }, { baseUrl: BASE_URL, timeoutMs: 15000 })
const byName = Object.fromEntries(tools.map((t) => [t.name, t]))

const EXPECTED = [
  'draftbox_write_article',
  'draftbox_typeset',
  'draftbox_save_draft',
  'draftbox_list_drafts',
  'draftbox_get_draft',
  'draftbox_illustrate',
  'draftbox_search_images',
  'draftbox_video_status',
]

let pass = 0
let fail = 0
function check(label, cond, extra = '') {
  console.log(`${cond ? '  PASS' : '  FAIL'}  ${label}${extra ? '  (' + extra + ')' : ''}`)
  cond ? pass++ : fail++
}

console.log(`\n== dsh-draftbox 工具层自测  base=${BASE_URL} ==`)

// ---- 契约校验：8 个工具齐全，且都有 description/render/execute ----
const names = tools.map((t) => t.name)
const missing = EXPECTED.filter((n) => !names.includes(n))
const extra = names.filter((n) => !EXPECTED.includes(n))
check('工具齐全 (8 个, 无缺漏)', missing.length === 0 && extra.length === 0,
  missing.length ? '缺:' + missing.join(',') : (extra.length ? '多:' + extra.join(',') : ''))
check('每个工具都有 description', tools.every((t) => typeof t.description === 'string' && t.description.length > 0))
check('每个工具都有 output.render', tools.every((t) => typeof (t.output || {}).render === 'function'))
check('每个工具都有 async execute', tools.every((t) => typeof t.execute === 'function'))

// ---- 真实 HTTP 调用（不依赖 LLM key）----
const uniq = 'smoke_' + Date.now()
let draftFile = null

// draftbox_list_drafts
try {
  const v = await byName['draftbox_list_drafts'].execute({})
  check('draftbox_list_drafts -> drafts[]', Array.isArray(v.drafts), `count=${(v.drafts || []).length}`)
  if (Array.isArray(v.drafts) && v.drafts.length) draftFile = v.drafts[0].filename
} catch (e) { check('draftbox_list_drafts', false, e.message) }

// draftbox_save_draft
try {
  const v = await byName['draftbox_save_draft'].execute({ title: uniq, content: '# 自测草稿\n\n由 tool-smoke 创建，会自动清理。', html: '<h1>自测草稿</h1>' })
  check('draftbox_save_draft -> ok+filename', v.ok === true && typeof v.filename === 'string', v.filename || '')
} catch (e) { check('draftbox_save_draft', false, e.message) }

// draftbox_get_draft（读刚存的）
try {
  const v = await byName['draftbox_get_draft'].execute({ filename: uniq + '.json' })
  // 后端返回 { title, markdown, html, updated_at }
  check('draftbox_get_draft -> title+markdown', !!v.title && typeof v.markdown === 'string' && v.title === uniq, `title=${v.title}`)
} catch (e) { check('draftbox_get_draft', false, e.message) }

// draftbox_typeset
try {
  const v = await byName['draftbox_typeset'].execute({ markdown: '# 标题\n\n正文。', theme: 'premium' })
  check('draftbox_typeset -> html_len>0', !v.error && (v.html || '').length > 0, `html_len=${(v.html || '').length}`)
} catch (e) { check('draftbox_typeset', false, e.message) }

// draftbox_search_images（Pexels）
// 注意：Pexels 限流(429/每小时200次) 是环境性抖动，后端会吞错返回空 images + error。
// 插件契约断言：返回结构必须是 {images: []}；有无结果都不算插件失败。
try {
  const v = await byName['draftbox_search_images'].execute({ query: 'ocean', count: 3 })
  const okShape = Array.isArray(v.images)
  const hasResults = okShape && v.images.length > 0
  const note = hasResults ? `n=${v.images.length}` : (v.error || '空结果(可能 Pexels 限流)')
  check('draftbox_search_images -> 契约 {images:[]}', okShape, note)
  if (!okShape) { check('draftbox_search_images', false, '返回非数组') }
} catch (e) { check('draftbox_search_images', false, e.message) }

// ---- 清理刚创建的测试草稿 ----
try {
  const r = await fetch(`${BASE_URL}/api/drafts/${encodeURIComponent(uniq + '.json')}`, { method: 'DELETE' })
  check('清理测试草稿', r.ok, `status=${r.status}`)
} catch (e) { check('清理测试草稿', false, e.message) }

console.log(`\n== 结果: ${pass} 通过 / ${fail} 失败 ==`)
process.exit(fail === 0 ? 0 : 1)
