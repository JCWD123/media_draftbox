import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'
import 'highlight.js/styles/github.css'

export const API = '/api'

// 全局 markdown-it 实例（开启微信兼容的 html + 代码高亮）
export const md = new MarkdownIt({
  html: true, linkify: true, typographer: true,
  highlight: (str, lang) => {
    if (lang && hljs.getLanguage(lang)) return '<pre class="hljs"><code>' + hljs.highlight(str, { language: lang }).value + '</code></pre>'
    return '<pre class="hljs"><code>' + md.utils.escapeHtml(str) + '</code></pre>'
  }
})

// 微信预览样式（排版转换预览 + AI 结果渲染共用）
export const WECHAT_CSS = `
  body{font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;font-size:16px;line-height:1.8;color:#333}
  h1{font-size:24px;font-weight:bold;margin:20px 0 10px}h2{font-size:20px;font-weight:bold;margin:16px 0 8px}
  h3{font-size:18px;font-weight:bold;margin:12px 0 6px}p{margin:0 0 16px;line-height:1.8}
  blockquote{margin:16px 0;padding:12px 16px;border-left:4px solid #1a73e8;background:#f8f9fa}
  code{background:#f6f8fa;padding:2px 6px;border-radius:3px;font-size:14px}
  pre{background:#f6f8fa;padding:16px;border-radius:6px;overflow-x:auto}pre code{background:none;padding:0}
  ul,ol{margin:12px 0;padding-left:24px}li{margin:4px 0}img{max-width:100%;height:auto}
  table{width:100%;border-collapse:collapse;margin:16px 0}th,td{border:1px solid #ddd;padding:8px 12px}th{background:#f8f9fa}
`

// 默认图片（图片搜索页面初始展示）
export const DEFAULT_IMAGES = [
  { id: 1, url: 'https://images.pexels.com/photos/3861969/pexels-photo-3861969.jpeg', thumb: 'https://images.pexels.com/photos/3861969/pexels-photo-3861969.jpeg?auto=compress&cs=tinysrgb&h=350', alt: 'Technology', author: 'Pexels' },
  { id: 2, url: 'https://images.pexels.com/photos/1181298/pexels-photo-1181298.jpeg', thumb: 'https://images.pexels.com/photos/1181298/pexels-photo-1181298.jpeg?auto=compress&cs=tinysrgb&h=350', alt: 'Coding', author: 'Pexels' },
  { id: 3, url: 'https://images.pexels.com/photos/2582937/pexels-photo-2582937.jpeg', thumb: 'https://images.pexels.com/photos/2582937/pexels-photo-2582937.jpeg?auto=compress&cs=tinysrgb&h=350', alt: 'AI', author: 'Pexels' },
  { id: 4, url: 'https://images.pexels.com/photos/546819/pexels-photo-546819.jpeg', thumb: 'https://images.pexels.com/photos/546819/pexels-photo-546819.jpeg?auto=compress&cs=tinysrgb&h=350', alt: 'Laptop', author: 'Pexels' },
  { id: 5, url: 'https://images.pexels.com/photos/325229/pexels-photo-325229.jpeg', thumb: 'https://images.pexels.com/photos/325229/pexels-photo-325229.jpeg?auto=compress&cs=tinysrgb&h=350', alt: 'Workspace', author: 'Pexels' },
  { id: 6, url: 'https://images.pexels.com/photos/11035544/pexels-photo-11035544.jpeg', thumb: 'https://images.pexels.com/photos/11035544/pexels-photo-11035544.jpeg?auto=compress&cs=tinysrgb&h=350', alt: 'Writing', author: 'Pexels' },
]

// 新闻分类颜色（热点新闻 Tab）
export const CATEGORY_COLORS = {
  'FINANCE': '#FF6B6B', 'TECH': '#4ECDC4', 'SOCIAL': '#45B7D1',
  'DEVELOPER': '#96CEB4', 'VIDEO': '#DDA0DD', 'COMMUNITY': '#A8E6CF', 'KNOWLEDGE': '#FFD93D'
}

// 通用 fetch helper（解包 { data: ... } 并统一错误处理）
export async function api(path, options = {}) {
  const r = await fetch(`${API}${path}`, options)
  const json = await r.json().catch(() => ({}))
  return json
}

// 通用 alert（后续可替换为 toast 组件）
export function notify(msg) {
  alert(msg)
}
