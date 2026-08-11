import { useState, useEffect, useRef } from 'react'
import { api, md, notify } from '../lib/shared'

export default function AiWriteTab({ onOpenConvert, onSaveDraft }) {
  const [topic, setTopic] = useState('')
  const [result, setResult] = useState('')
  const [html, setHtml] = useState('')
  const [title, setTitle] = useState('')
  const [tags, setTags] = useState([])
  const [vertical, setVertical] = useState('')
  const [warnings, setWarnings] = useState([])
  const [loading, setLoading] = useState(false)
  const [withImages, setWithImages] = useState(true)
  const [withVideo, setWithVideo] = useState(false)
  const [news, setNews] = useState([])
  const [newsCategory, setNewsCategory] = useState('TECH')
  const [categories, setCategories] = useState([])
  const [selected, setSelected] = useState(new Set())
  const [draftId, setDraftId] = useState('')
  const [videoStatus, setVideoStatus] = useState('')
  const pollTimer = useRef(null)

  useEffect(() => {
    api('/news/categories').then(d => {
      const cats = (d.data || []).map(c => ({ id: c.category_code, name: c.category_name }))
      setCategories(cats)
    }).catch(() => {})
  }, [])

  const loadNews = async (cat, initial = false) => {
    setNewsCategory(cat)
    if (!initial && news.length > 0) return
    try {
      const d = await api('/news/list', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ category: cat, page: 1, page_size: 20 })
      })
      setNews(d.news || [])
    } catch (e) { setNews([]) }
  }
  useEffect(() => { loadNews('TECH', true) }, [])

  const toggleNews = (id) => {
    const next = new Set(selected)
    if (next.has(id)) next.delete(id)
    else {
      if (next.size >= 10) { notify('最多选 10 条新闻'); return }
      next.add(id)
    }
    setSelected(next)
  }

  const generate = async () => {
    if (!topic.trim()) { notify('请输入话题/核心思路'); return }
    setLoading(true)
    setResult(''); setHtml(''); setTags([]); setWarnings([]); setVideoStatus('')
    try {
      const d = await api('/write/generate', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          topic: topic.trim(), news_ids: [...selected],
          with_images: withImages, with_video: withVideo, max_images: 4, max_videos: 1
        })
      })
      if (!d.success) { setWarnings([d.error]); setLoading(false); return }
      setResult(d.content); setHtml(d.html); setTags(d.tags || []); setTitle(d.title || ''); setDraftId(d.draft_id)
      if (d.vertical_check?.drifted) setVertical(`⚠ 垂直度已校准: ${d.vertical_check.note || ''}`)
      else if (d.vertical_check?.domain) setVertical(`✓ 垂直领域: ${d.vertical_check.domain}`)
      else setVertical('')
      setWarnings(d.warnings || [])
      if (d.video_pending) pollVideo(d.draft_id)
    } catch (e) { setWarnings(['生成失败: ' + e.message]) }
    setLoading(false)
  }

  const pollVideo = (draftId) => {
    if (pollTimer.current) clearInterval(pollTimer.current)
    pollTimer.current = setInterval(async () => {
      try {
        const d = await api(`/write/media-status?draft_id=${draftId}`)
        if (d.status === 'done') {
          clearInterval(pollTimer.current)
          setVideoStatus('✅ 视频已生成')
          if (d.html) setHtml(d.html)
        } else if (d.status === 'failed') {
          clearInterval(pollTimer.current)
          setVideoStatus('❌ 视频生成失败: ' + (d.error || ''))
        } else {
          setVideoStatus('⏳ 视频生成中（约 1-5 分钟）...')
        }
      } catch (e) { clearInterval(pollTimer.current) }
    }, 5000)
  }

  useEffect(() => () => { if (pollTimer.current) clearInterval(pollTimer.current) }, [])

  const openConvert = () => {
    onOpenConvert(result)
  }

  const saveDraft = () => {
    onSaveDraft(title || topic || 'AI生成文章', result)
  }

  return (
    <div className="panel full">
      <h2>🤖 AI 写作（文字 + 图片 + 视频）</h2>
      <div className="toolbar">
        <input className="topic-input" value={topic} onChange={e => setTopic(e.target.value)} placeholder="输入话题/核心思路（必填）..." style={{ flex: 1 }}
          onKeyDown={e => e.key === 'Enter' && generate()} />
        <button className="btn-primary" onClick={generate} disabled={loading}>{loading ? '⏳ 生成中...' : '🚀 生成'}</button>
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
            {categories.map(c => (
              <button key={c.id} className={`cat-tab ${newsCategory === c.id ? 'active' : ''}`}
                onClick={() => loadNews(c.id)}>{c.name}</button>
            ))}
          </div>
          <span className="selected-count">已选 {selected.size} 条
            {selected.size > 0 && <button className="link-btn" onClick={() => setSelected(new Set())}>清空</button>}
          </span>
        </div>
        <div className="news-select-list">
          {news.map(item => (
            <label key={item.id} className="news-check-item">
              <input type="checkbox" checked={selected.has(item.id)} onChange={() => toggleNews(item.id)} />
              <span className="news-check-title">{item.title}</span>
              <span className="news-check-source">{item.source}</span>
            </label>
          ))}
          {news.length === 0 && <div className="news-empty">点击上方分类加载新闻</div>}
        </div>
      </div>
      {/* 标签 + 垂直度 */}
      {tags.length > 0 && (
        <div className="tag-bar">
          {tags.map(t => <span key={t} className="tag">#{t}</span>)}
          {vertical && <span className="vertical-note">{vertical}</span>}
        </div>
      )}
      {warnings.length > 0 && (
        <div className="warnings">
          {warnings.map((w, i) => <div key={i}>⚠ {w}</div>)}
        </div>
      )}
      {/* 生成结果 */}
      {result && (
        <div className="ai-result">
          <div className="panel-head">
            <h3>{title}</h3>
          </div>
          <div className="toolbar">
            <button className="btn-primary" onClick={openConvert}>📐 转为排版</button>
            <button className="btn" onClick={saveDraft}>💾 保存草稿</button>
          </div>
          <div className="preview" dangerouslySetInnerHTML={{ __html: html || md.render(result) }} />
        </div>
      )}
    </div>
  )
}
