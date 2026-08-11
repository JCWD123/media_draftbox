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
  body{font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;font-size:16px;line-height:1.8;color:#333}
  h1{font-size:24px;font-weight:bold;margin:20px 0 10px}h2{font-size:20px;font-weight:bold;margin:16px 0 8px}
  h3{font-size:18px;font-weight:bold;margin:12px 0 6px}p{margin:0 0 16px;line-height:1.8}
  blockquote{margin:16px 0;padding:12px 16px;border-left:4px solid #1a73e8;background:#f8f9fa}
  code{background:#f6f8fa;padding:2px 6px;border-radius:3px;font-size:14px}
  pre{background:#f6f8fa;padding:16px;border-radius:6px;overflow-x:auto}pre code{background:none;padding:0}
  ul,ol{margin:12px 0;padding-left:24px}li{margin:4px 0}img{max-width:100%;height:auto}
  table{width:100%;border-collapse:collapse;margin:16px 0}th,td{border:1px solid #ddd;padding:8px 12px}th{background:#f8f9fa}
`

// 默认图片（用于图片搜索页面初始化）
const DEFAULT_IMAGES = [
  { id: 1, url: 'https://images.pexels.com/photos/3861969/pexels-photo-3861969.jpeg', thumb: 'https://images.pexels.com/photos/3861969/pexels-photo-3861969.jpeg?auto=compress&cs=tinysrgb&h=350', alt: 'Technology', author: 'Pexels' },
  { id: 2, url: 'https://images.pexels.com/photos/1181298/pexels-photo-1181298.jpeg', thumb: 'https://images.pexels.com/photos/1181298/pexels-photo-1181298.jpeg?auto=compress&cs=tinysrgb&h=350', alt: 'Coding', author: 'Pexels' },
  { id: 3, url: 'https://images.pexels.com/photos/2582937/pexels-photo-2582937.jpeg', thumb: 'https://images.pexels.com/photos/2582937/pexels-photo-2582937.jpeg?auto=compress&cs=tinysrgb&h=350', alt: 'AI', author: 'Pexels' },
  { id: 4, url: 'https://images.pexels.com/photos/546819/pexels-photo-546819.jpeg', thumb: 'https://images.pexels.com/photos/546819/pexels-photo-546819.jpeg?auto=compress&cs=tinysrgb&h=350', alt: 'Laptop', author: 'Pexels' },
  { id: 5, url: 'https://images.pexels.com/photos/325229/pexels-photo-325229.jpeg', thumb: 'https://images.pexels.com/photos/325229/pexels-photo-325229.jpeg?auto=compress&cs=tinysrgb&h=350', alt: 'Workspace', author: 'Pexels' },
  { id: 6, url: 'https://images.pexels.com/photos/11035544/pexels-photo-11035544.jpeg', thumb: 'https://images.pexels.com/photos/11035544/pexels-photo-11035544.jpeg?auto=compress&cs=tinysrgb&h=350', alt: 'Writing', author: 'Pexels' },
]

// 新闻分类颜色
const CATEGORY_COLORS = {
  'FINANCE': '#FF6B6B', 'TECH': '#4ECDC4', 'SOCIAL': '#45B7D1',
  'DEVELOPER': '#96CEB4', 'VIDEO': '#DDA0DD', 'COMMUNITY': '#A8E6CF', 'KNOWLEDGE': '#FFD93D'
}

export default function App() {
  const [tab, setTab] = useState('convert')
  const [markdown, setMarkdown] = useState('# 标题\n\n这是测试内容')
  const [html, setHtml] = useState('')
  const [theme, setTheme] = useState('professional')
  const [themeList] = useState([
    { id: 'professional', name: '专业简洁' }, { id: 'minimal', name: '极简' },
    { id: 'github', name: 'GitHub风格' }, { id: 'newspaper', name: '报纸风格' }, { id: 'bold-navy', name: '深蓝粗体' },
  ])
  const [imgQuery, setImgQuery] = useState('')
  const [images, setImages] = useState(DEFAULT_IMAGES)
  const [drafts, setDrafts] = useState([])
  const [draftTitle, setDraftTitle] = useState('')
  const [news, setNews] = useState([])
  const [newsCategory, setNewsCategory] = useState('TECH')
  const [newsCategories, setNewsCategories] = useState([])
  const [newsLoading, setNewsLoading] = useState(false)

  // AI 写作状态
  const [aiTopic, setAiTopic] = useState('')
  const [aiResult, setAiResult] = useState('')
  const [aiHtml, setAiHtml] = useState('')
  const [aiTitle, setAiTitle] = useState('')
  const [aiTags, setAiTags] = useState([])
  const [aiVertical, setAiVertical] = useState('')
  const [aiWarnings, setAiWarnings] = useState([])
  const [aiLoading, setAiLoading] = useState(false)
  const [withImages, setWithImages] = useState(true)
  const [withVideo, setWithVideo] = useState(false)
  const [aiNews, setAiNews] = useState([])
  const [aiNewsCategory, setAiNewsCategory] = useState('TECH')
  const [selectedNews, setSelectedNews] = useState(new Set())
  const [aiDraftId, setAiDraftId] = useState('')
  const [videoStatus, setVideoStatus] = useState('')

  useEffect(() => { setHtml(`<style>${WECHAT_CSS}</style><div>${md.render(markdown)}</div>`) }, [markdown])
  useEffect(() => { if (tab === 'drafts') fetch(`${API}/drafts`).then(r => r.json()).then(d => setDrafts(d.drafts || [])).catch(() => {}) }, [tab])
  useEffect(() => {
    fetch(`${API}/news/categories`).then(r => r.json()).then(d => {
      const cats = (d.data || []).map(c => ({ id: c.category_code, name: c.category_name, icon: c.icon, color: c.color }))
      setNewsCategories(cats)
    }).catch(() => {})
  }, [])
  useEffect(() => { if (tab === 'ai' && aiNews.length === 0) loadAiNews('TECH') }, [tab])

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

  const searchImages = async () => {
    if (!imgQuery) return
    try {
      const r = await fetch(`${API}/images/search`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ query: imgQuery, count: 12 }) })
      const d = await r.json()
      setImages(d.images || [])
    } catch (e) { setImages([]) }
  }

  const saveDraft = async () => {
    if (!draftTitle) return
    await fetch(`${API}/drafts`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ title: draftTitle, content: markdown }) })
    setDraftTitle('')
    fetch(`${API}/drafts`).then(r => r.json()).then(d => setDrafts(d.drafts || []))
  }

  const copyToClipboard = () => {
    navigator.clipboard.write([new ClipboardItem({ 'text/html': new Blob([html], { type: 'text/html' }) })])
    alert('已复制')
  }

  // ---------- AI 写作 ----------
  const loadAiNews = async (cat) => {
    setAiNewsCategory(cat)
    try {
      const r = await fetch(`${API}/news/list`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ category: cat, page: 1, page_size: 20 }) })
      const d = await r.json()
      setAiNews(d.news || [])
    } catch (e) { setAiNews([]) }
  }

  const toggleNews = (id) => {
    const next = new Set(selectedNews)
    if (next.has(id)) { next.delete(id) }
    else {
      if (next.size >= 10) { alert('最多选 10 条'); return }
      next.add(id)
    }
    setSelectedNews(next)
  }

  const generateArticle = async () => {
    if (!aiTopic.trim()) { alert('请输入话题/核心思路'); return }
    setAiLoading(true); setAiResult(''); setAiHtml(''); setAiTags([]); setAiWarnings([]); setVideoStatus('')
    try {
      const r = await fetch(`${API}/write/generate`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          topic: aiTopic, news_ids: [...selectedNews],
          with_images: withImages, with_video: withVideo, max_images: 4, max_videos: 1
        })
      })
      const d = await r.json()
      if (!d.success) { setAiWarnings([d.error]); return }
      setAiResult(d.content); setAiHtml(d.html); setAiTags(d.tags || []); setAiTitle(d.title || '')
      setAiDraftId(d.draft_id)
      if (d.vertical_check?.drifted) setAiVertical(`⚠ 垂直度已校准: ${d.vertical_check.note || ''}`)
      else if (d.vertical_check?.domain) setAiVertical(`✓ 垂直领域: ${d.vertical_check.domain}`)
      else setAiVertical('')
      setAiWarnings(d.warnings || [])
      if (d.video_pending) pollVideoStatus(d.draft_id)
    } catch (e) { setAiWarnings(['生成失败: ' + e.message]) }
    setAiLoading(false)
  }

  const pollVideoStatus = (draftId) => {
    const timer = setInterval(async () => {
      try {
        const r = await fetch(`${API}/write/media-status?draft_id=${draftId}`)
        const d = await r.json()
        if (d.status === 'done') {
          clearInterval(timer)
          setVideoStatus('✅ 视频已生成')
          if (d.html) setAiHtml(d.html)
        } else if (d.status === 'failed') {
          clearInterval(timer)
          setVideoStatus('❌ 视频生成失败: ' + (d.error || ''))
        } else {
          setVideoStatus('⏳ 视频生成中（约 1-5 分钟）...')
        }
      } catch (e) { clearInterval(timer) }
    }, 5000)
  }

  const saveAiDraft = async () => {
    const title = aiTitle || aiTopic || 'AI生成文章'
    await fetch(`${API}/drafts`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ title, content: aiResult }) })
    alert('已保存草稿: ' + title)
  }

  const tabs = [
    { id: 'convert', label: '📝 排版转换' },
    { id: 'news', label: '🔥 热点新闻' },
    { id: 'ai', label: '🤖 AI写作' },
    { id: 'images', label: '🖼️ 图片搜索' },
    { id: 'drafts', label: '📄 草稿管理' }
  ]

  return (
    <div className="app">
      <header className="header">
        <h1>📝 DraftBox</h1>
        <span className="subtitle">会学习的 AI 写作助手（文字 + 图片 + 视频）</span>
      </header>
      <nav className="nav">
        {tabs.map(t => (
          <button key={t.id} className={tab === t.id ? 'nav-btn active' : 'nav-btn'} onClick={() => setTab(t.id)}>
            {t.label}
          </button>
        ))}
      </nav>
      <main className="main">
        {/* 排版转换 */}
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
              <div className="preview" dangerouslySetInnerHTML={{ __html: html }} />
            </div>
          </div>
        )}

        {/* 热点新闻 - 仿VPS风格 */}
        {tab === 'news' && (
          <div className="news-layout">
            <div className="news-sidebar">
              <h3>新闻分类</h3>
              {newsCategories.map(c => (
                <div key={c.id} className={`news-cat-item ${newsCategory === c.id ? 'active' : ''}`}
                  onClick={() => loadNews(c.id)}>
                  <span className="cat-dot" style={{ background: c.color || '#999' }}></span>
                  <span>{c.name}</span>
                </div>
              ))}
            </div>
            <div className="news-main">
              <div className="news-header">
                <h2>{newsCategories.find(c => c.id === newsCategory)?.name || '热点新闻'}</h2>
                <span className="news-count">{news.length} 条新闻</span>
              </div>
              {newsLoading ? (
                <div className="news-loading">加载中...</div>
              ) : (
                <div className="news-list">
                  {news.map((item, i) => (
                    <a key={i} className="news-card" href={item.link} target="_blank" rel="noopener noreferrer">
                      <div className="news-card-title">{item.title}</div>
                      <div className="news-card-meta">
                        <span className="news-source-badge" style={{ background: CATEGORY_COLORS[newsCategory] || '#999' }}>
                          {item.source}
                        </span>
                        <span className="news-date">{item.published}</span>
                      </div>
                    </a>
                  ))}
                  {news.length === 0 && <div className="news-empty">暂无新闻</div>}
                </div>
              )}
            </div>
          </div>
        )}

        {/* AI写作 - 三模态（文字+图片+视频） */}
        {tab === 'ai' && (
          <div className="panel full">
            <h2>🤖 AI 写作（文字 + 图片 + 视频）</h2>
            <div className="toolbar">
              <input value={aiTopic} onChange={e => setAiTopic(e.target.value)} placeholder="输入话题/核心思路（必填）..." style={{ flex: 1 }} />
              <button onClick={generateArticle} disabled={aiLoading}>{aiLoading ? '生成中...' : '🚀 生成'}</button>
            </div>
            <div className="toolbar">
              <label className="media-opt"><input type="checkbox" checked={withImages} onChange={e => setWithImages(e.target.checked)} /> 生成配图（默认）</label>
              <label className="media-opt"><input type="checkbox" checked={withVideo} onChange={e => setWithVideo(e.target.checked)} /> 生成视频（约1-5分钟）</label>
              {videoStatus && <span className="video-status">{videoStatus}</span>}
            </div>
            {/* 新闻素材勾选 */}
            <div className="news-select">
              <div className="news-select-header">
                <h3>📰 新闻素材勾选（可选，最多 10 条）</h3>
                <div className="news-cat-tabs">
                  {newsCategories.map(c => (
                    <button key={c.id} className={`cat-tab ${aiNewsCategory === c.id ? 'active' : ''}`}
                      onClick={() => loadAiNews(c.id)}>{c.name}</button>
                  ))}
                </div>
                <span className="selected-count">已选 {selectedNews.size} 条
                  {selectedNews.size > 0 && <button className="link-btn" onClick={() => setSelectedNews(new Set())}>清空</button>}
                </span>
              </div>
              <div className="news-select-list">
                {aiNews.map(item => (
                  <label key={item.id} className="news-check-item">
                    <input type="checkbox" checked={selectedNews.has(item.id)} onChange={() => toggleNews(item.id)} />
                    <span className="news-check-title">{item.title}</span>
                    <span className="news-check-source">{item.source}</span>
                  </label>
                ))}
                {aiNews.length === 0 && <div className="news-empty">点击上方分类加载新闻</div>}
              </div>
            </div>
            {/* 标签 + 垂直度 */}
            {aiTags.length > 0 && (
              <div className="tag-bar">
                {aiTags.map(t => <span key={t} className="tag">#{t}</span>)}
                {aiVertical && <span className="vertical-note">{aiVertical}</span>}
              </div>
            )}
            {aiWarnings.length > 0 && (
              <div className="warnings">
                {aiWarnings.map((w, i) => <div key={i}>⚠ {w}</div>)}
              </div>
            )}
            {/* 生成结果 */}
            {aiResult && (
              <div className="ai-result">
                <div className="toolbar">
                  <button onClick={() => { setMarkdown(aiResult); setTab('convert') }}>📐 转为排版</button>
                  <button onClick={saveAiDraft}>💾 保存草稿</button>
                </div>
                <div className="preview" dangerouslySetInnerHTML={{ __html: aiHtml || md.render(aiResult) }} />
              </div>
            )}
          </div>
        )}

        {/* 图片搜索 - 默认显示图片 */}
        {tab === 'images' && (
          <div className="panel full">
            <h2>🖼️ 图片搜索</h2>
            <div className="toolbar">
              <input value={imgQuery} onChange={e => setImgQuery(e.target.value)} placeholder="搜索图片..."
                onKeyDown={e => e.key === 'Enter' && searchImages()} />
              <button onClick={searchImages}>搜索</button>
            </div>
            <div className="img-grid">
              {images.map(img => (
                <div key={img.id} className="img-card" onClick={() => navigator.clipboard.writeText(`![${img.alt}](${img.url})`)}>
                  <img src={img.thumb} alt={img.alt} />
                  <div className="img-author">{img.author}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 草稿管理 */}
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
