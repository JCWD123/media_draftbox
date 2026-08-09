import React, { useState, useEffect, useRef } from 'react'
import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'
import 'highlight.js/styles/github.css'

const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true,
  highlight: (str, lang) => {
    if (lang && hljs.getLanguage(lang)) {
      return '<pre class="hljs"><code>' + hljs.highlight(str, { language: lang }).value + '</code></pre>'
    }
    return '<pre class="hljs"><code>' + md.utils.escapeHtml(str) + '</code></pre>'
  }
})

const API = '/api'

// 微信兼容CSS（借鉴 wewrite）
const WECHAT_CSS = `
  body { font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei", sans-serif; font-size: 16px; line-height: 1.8; color: #333; }
  h1 { font-size: 24px; font-weight: bold; margin: 20px 0 10px; }
  h2 { font-size: 20px; font-weight: bold; margin: 16px 0 8px; }
  h3 { font-size: 18px; font-weight: bold; margin: 12px 0 6px; }
  p { margin: 0 0 16px; line-height: 1.8; }
  blockquote { margin: 16px 0; padding: 12px 16px; border-left: 4px solid #1a73e8; background: #f8f9fa; }
  code { background: #f6f8fa; padding: 2px 6px; border-radius: 3px; font-size: 14px; }
  pre { background: #f6f8fa; padding: 16px; border-radius: 6px; overflow-x: auto; }
  pre code { background: none; padding: 0; }
  ul, ol { margin: 12px 0; padding-left: 24px; }
  li { margin: 4px 0; }
  img { max-width: 100%; height: auto; }
  table { width: 100%; border-collapse: collapse; margin: 16px 0; }
  th, td { border: 1px solid #ddd; padding: 8px 12px; }
  th { background: #f8f9fa; }
`

export default function App() {
  const [tab, setTab] = useState('convert')
  const [markdown, setMarkdown] = useState(`# 标题

这是测试内容，支持**加粗**和*斜体*。

## 代码块

\`\`\`python
print('Hello World')
\`\`\`

> 引用内容

1. 第一点
2. 第二点`)
  const [theme, setTheme] = useState('professional')
  const [html, setHtml] = useState('')
  const [themes, setThemes] = useState([])
  const [aiTopic, setAiTopic] = useState('')
  const [aiResult, setAiResult] = useState('')
  const [imgQuery, setImgQuery] = useState('')
  const [images, setImages] = useState([])
  const [drafts, setDrafts] = useState([])
  const [draftTitle, setDraftTitle] = useState('')
  const previewRef = useRef(null)

  // 主题列表
  const themeList = [
    { id: 'professional', name: '专业简洁', accent: '#1a73e8' },
    { id: 'minimal', name: '极简', accent: '#333' },
    { id: 'github', name: 'GitHub风格', accent: '#0969da' },
    { id: 'newspaper', name: '报纸风格', accent: '#c41d35' },
    { id: 'bold-navy', name: '深蓝粗体', accent: '#1a365d' },
  ]

  // 转换Markdown（前端直接渲染）
  useEffect(() => {
    const htmlContent = md.render(markdown)
    setHtml(`<style>${WECHAT_CSS}</style><div>${htmlContent}</div>`)
  }, [markdown])

  // 加载草稿
  useEffect(() => {
    if (tab === 'drafts') {
      fetch(`${API}/drafts`).then(r => r.json()).then(d => setDrafts(d.drafts || [])).catch(() => {})
    }
  }, [tab])

  // 保存草稿
  const saveDraft = async () => {
    if (!draftTitle) return
    await fetch(`${API}/drafts`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: draftTitle, content: markdown })
    })
    setDraftTitle('')
    fetch(`${API}/drafts`).then(r => r.json()).then(d => setDrafts(d.drafts || []))
  }

  // 搜索图片
  const searchImages = async () => {
    if (!imgQuery) return
    try {
      const r = await fetch(`https://api.pexels.com/v1/search?query=${encodeURIComponent(imgQuery)}&per_page=12`, {
        headers: { Authorization: 'ivibKq6WluQyUjzHrwRpE21wGRUArAuUI0fgMnvNPNslz49LKswz6Oo0' }
      })
      const d = await r.json()
      setImages(d.photos || [])
    } catch (e) { console.error(e) }
  }

  // 复制到剪贴板
  const copyToClipboard = () => {
    const blob = new Blob([html], { type: 'text/html' })
    const item = new ClipboardItem({ 'text/html': blob })
    navigator.clipboard.write([item])
    alert('已复制到剪贴板')
  }

  const tabs = [
    { id: 'convert', label: '📝 排版转换' },
    { id: 'news', label: '🔥 热点新闻' },
    { id: 'ai', label: '🤖 AI写作' },
    { id: 'images', label: '🖼️ 图片搜索' },
    { id: 'drafts', label: '📄 草稿管理' },
  ]

  return (
    <div className="app">
      <header className="header">
        <h1>📝 DraftBox</h1>
        <span className="subtitle">会学习的 AI 写作助手</span>
      </header>
      <nav className="nav">
        {tabs.map(t => (
          <button key={t.id} className={tab === t.id ? 'nav-btn active' : 'nav-btn'} onClick={() => setTab(t.id)}>
            {t.label}
          </button>
        ))}
      </nav>
      <main className="main">
        {tab === 'convert' && (
          <div className="split">
            <div className="panel">
              <h2>Markdown</h2>
              <div className="toolbar">
                <select value={theme} onChange={e => setTheme(e.target.value)}>
                  {themeList.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
                </select>
                <button onClick={copyToClipboard}>📋 复制HTML</button>
              </div>
              <textarea value={markdown} onChange={e => setMarkdown(e.target.value)} />
            </div>
            <div className="panel">
              <h2>预览</h2>
              <div className="preview" ref={previewRef} dangerouslySetInnerHTML={{ __html: html }} />
            </div>
          </div>
        )}
        {tab === 'news' && (
          <div className="panel full">
            <h2>🔥 热点新闻</h2>
            <p className="muted">接入新闻 API 后可用</p>
          </div>
        )}
        {tab === 'ai' && (
          <div className="panel full">
            <h2>🤖 AI 写作</h2>
            <div className="toolbar">
              <input value={aiTopic} onChange={e => setAiTopic(e.target.value)} placeholder="输入话题..." />
              <button onClick={() => setAiResult(`关于「${aiTopic}」的文章生成中...`)}>生成</button>
            </div>
            {aiResult && <div className="result">{aiResult}</div>}
          </div>
        )}
        {tab === 'images' && (
          <div className="panel full">
            <h2>🖼️ 图片搜索</h2>
            <div className="toolbar">
              <input value={imgQuery} onChange={e => setImgQuery(e.target.value)} placeholder="搜索图片..." onKeyDown={e => e.key === 'Enter' && searchImages()} />
              <button onClick={searchImages}>搜索</button>
            </div>
            <div className="img-grid">
              {images.map(img => (
                <img key={img.id} src={img.src.medium} alt={img.alt}
                  onClick={() => navigator.clipboard.writeText(`![${img.alt}](${img.src.large})`)} />
              ))}
            </div>
          </div>
        )}
        {tab === 'drafts' && (
          <div className="panel full">
            <h2>📄 草稿管理</h2>
            <div className="toolbar">
              <input value={draftTitle} onChange={e => setDraftTitle(e.target.value)} placeholder="草稿标题..." />
              <button onClick={saveDraft}>保存</button>
            </div>
            <div className="draft-list">
              {drafts.map(d => (
                <div key={d.filename} className="draft-item"
                  onClick={() => fetch(`${API}/drafts/${d.filename}`).then(r => r.json()).then(d => setMarkdown(d.content))}>
                  {d.title}
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
