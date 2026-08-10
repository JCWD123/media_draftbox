import React, { useState, useEffect } from 'react'
import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'
import 'highlight.js/styles/github.css'

const md = new MarkdownIt({
  html: true, linkify: true, typographer: true,
  highlight: (str, lang) => {
    if (lang && hljs.getLanguage(lang)) return '<pre class="hljs"><code>' + hljs.highlight(str, { language: lang }).value + '</code></pre>'
    return '<pre class="hljs"><code>' + md.utils.escapeHtml(str) + '</code></pre>'
  }
})

const API = '/api'

const WECHAT_CSS = `
  body { font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei", sans-serif; font-size: 16px; line-height: 1.8; color: #333; }
  h1 { font-size: 24px; font-weight: bold; margin: 20px 0 10px; } h2 { font-size: 20px; font-weight: bold; margin: 16px 0 8px; }
  h3 { font-size: 18px; font-weight: bold; margin: 12px 0 6px; } p { margin: 0 0 16px; line-height: 1.8; }
  blockquote { margin: 16px 0; padding: 12px 16px; border-left: 4px solid #1a73e8; background: #f8f9fa; }
  code { background: #f6f8fa; padding: 2px 6px; border-radius: 3px; font-size: 14px; }
  pre { background: #f6f8fa; padding: 16px; border-radius: 6px; overflow-x: auto; } pre code { background: none; padding: 0; }
  ul, ol { margin: 12px 0; padding-left: 24px; } li { margin: 4px 0; } img { max-width: 100%; height: auto; }
  table { width: 100%; border-collapse: collapse; margin: 16px 0; } th, td { border: 1px solid #ddd; padding: 8px 12px; } th { background: #f8f9fa; }
`

export default function App() {
  const [tab, setTab] = useState('convert')
  const [markdown, setMarkdown] = useState('# 标题\n\n这是测试内容')
  const [html, setHtml] = useState('')
  const [theme, setTheme] = useState('professional')
  const [themeList] = useState([
    { id: 'professional', name: '专业简洁' }, { id: 'minimal', name: '极简' },
    { id: 'github', name: 'GitHub风格' }, { id: 'newspaper', name: '报纸风格' }, { id: 'bold-navy', name: '深蓝粗体' },
  ])
  const [aiTopic, setAiTopic] = useState('')
  const [aiResult, setAiResult] = useState('')
  const [imgQuery, setImgQuery] = useState('')
  const [images, setImages] = useState([])
  const [drafts, setDrafts] = useState([])
  const [draftTitle, setDraftTitle] = useState('')
  const [news, setNews] = useState([])
  const [newsCategory, setNewsCategory] = useState('TECH')
  const [newsCategories, setNewsCategories] = useState([])
  const [newsLoading, setNewsLoading] = useState(false)

  useEffect(() => { setHtml(`<style>${WECHAT_CSS}</style><div>${md.render(markdown)}</div>`) }, [markdown])
  useEffect(() => { if (tab === 'drafts') fetch(`${API}/drafts`).then(r => r.json()).then(d => setDrafts(d.drafts || [])).catch(() => {}) }, [tab])
  useEffect(() => {
    fetch(`${API}/news/categories`).then(r => r.json()).then(d => {
      const cats = (d.data || []).map(c => ({ id: c.category_code, name: c.category_name, icon: c.icon }))
      setNewsCategories(cats)
    }).catch(() => {})
  }, [])

  const loadNews = async (cat) => {
    setNewsCategory(cat); setNewsLoading(true)
    try {
      const r = await fetch(`${API}/news/list`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ category: cat, page: 1, page_size: 20 }) })
      const d = await r.json()
      setNews(d.news || [])
    } catch (e) { setNews([]) }
    setNewsLoading(false)
  }

  useEffect(() => { if (tab === 'news') loadNews(newsCategory) }, [tab])

  const saveDraft = async () => { if (!draftTitle) return; await fetch(`${API}/drafts`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ title: draftTitle, content: markdown }) }); setDraftTitle(''); fetch(`${API}/drafts`).then(r => r.json()).then(d => setDrafts(d.drafts || [])) }
  const searchImages = async () => { if (!imgQuery) return; try { const r = await fetch(`${API}/images/search`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ query: imgQuery, count: 12 }) }); const d = await r.json(); setImages(d.images || []) } catch (e) { setImages([]) } }
  const copyToClipboard = () => { navigator.clipboard.write([new ClipboardItem({ 'text/html': new Blob([html], { type: 'text/html' }) })]); alert('已复制') }

  const tabs = [{ id: 'convert', label: '📝 排版转换' }, { id: 'news', label: '🔥 热点新闻' }, { id: 'ai', label: '🤖 AI写作' }, { id: 'images', label: '🖼️ 图片搜索' }, { id: 'drafts', label: '📄 草稿管理' }]

  return (
    <div className="app">
      <header className="header"><h1>📝 DraftBox</h1><span className="subtitle">会学习的 AI 写作助手</span></header>
      <nav className="nav">{tabs.map(t => <button key={t.id} className={tab === t.id ? 'nav-btn active' : 'nav-btn'} onClick={() => setTab(t.id)}>{t.label}</button>)}</nav>
      <main className="main">
        {tab === 'convert' && (<div className="split">
          <div className="panel"><h2>Markdown</h2><div className="toolbar"><select value={theme} onChange={e => setTheme(e.target.value)}>{themeList.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}</select><button onClick={copyToClipboard}>📋 复制HTML</button></div><textarea value={markdown} onChange={e => setMarkdown(e.target.value)} /></div>
          <div className="panel"><h2>预览</h2><div className="preview" dangerouslySetInnerHTML={{ __html: html }} /></div>
        </div>)}

        {tab === 'news' && (<div className="panel full">
          <h2>🔥 热点新闻</h2>
          <div className="toolbar">
            {newsCategories.map(c => <button key={c.id} onClick={() => loadNews(c.id)} style={{ background: newsCategory === c.id ? '#1a73e8' : '#f0f0f0', color: newsCategory === c.id ? '#fff' : '#333', border: 'none', borderRadius: 4, padding: '6px 12px', cursor: 'pointer' }}>{c.name}</button>)}
          </div>
          {newsLoading ? <p className="muted">加载中...</p> : (
            <div className="news-list">{news.map((item, i) => (
              <div key={i} className="news-item" onClick={() => { setMarkdown(`# ${item.title}\n\n${item.summary}\n\n来源：${item.source}`); setTab('convert') }}>
                <h3>{item.title}</h3><p className="muted">{item.summary}</p><span className="news-source">{item.source} · {item.published}</span>
              </div>
            ))}</div>
          )}
        </div>)}

        {tab === 'ai' && (<div className="panel full"><h2>🤖 AI 写作</h2><div className="toolbar"><input value={aiTopic} onChange={e => setAiTopic(e.target.value)} placeholder="输入话题..." /><button onClick={() => setAiResult(`关于「${aiTopic}」的文章生成中...`)}>生成</button></div>{aiResult && <div className="result">{aiResult}</div>}</div>)}

        {tab === 'images' && (<div className="panel full"><h2>🖼️ 图片搜索</h2><div className="toolbar"><input value={imgQuery} onChange={e => setImgQuery(e.target.value)} placeholder="搜索图片..." onKeyDown={e => e.key === 'Enter' && searchImages()} /><button onClick={searchImages}>搜索</button></div><div className="img-grid">{images.map(img => <img key={img.id} src={img.thumb} alt={img.alt} onClick={() => navigator.clipboard.writeText(`![${img.alt}](${img.url})`)} />)}</div></div>)}

        {tab === 'drafts' && (<div className="panel full"><h2>📄 草稿管理</h2><div className="toolbar"><input value={draftTitle} onChange={e => setDraftTitle(e.target.value)} placeholder="草稿标题..." /><button onClick={saveDraft}>保存</button></div><div className="draft-list">{drafts.map(d => <div key={d.filename} className="draft-item" onClick={() => fetch(`${API}/drafts/${d.filename}`).then(r => r.json()).then(d => setMarkdown(d.content))}>{d.title}</div>)}</div></div>)}
      </main>
    </div>
  )
}
