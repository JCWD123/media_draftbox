import { useState } from 'react'
import { api, DEFAULT_IMAGES, notify } from '../lib/shared'

export default function ImagesTab() {
  const [query, setQuery] = useState('')
  const [images, setImages] = useState(DEFAULT_IMAGES)
  const [loading, setLoading] = useState(false)

  const search = async () => {
    if (!query.trim()) return
    setLoading(true)
    try {
      const d = await api('/images/search', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: query.trim(), count: 12 })
      })
      setImages(d.images || [])
    } catch (e) { setImages([]) }
    setLoading(false)
  }

  const copyUrl = async (img) => {
    try {
      await navigator.clipboard.writeText(`![${img.alt}](${img.url})`)
      notify('✅ 已复制图片 Markdown')
    } catch (e) { notify('复制失败: ' + e.message) }
  }

  return (
    <div className="panel full">
      <h2>🖼️ 图片搜索</h2>
      <div className="toolbar">
        <input value={query} onChange={e => setQuery(e.target.value)} placeholder="搜索图片..."
          onKeyDown={e => e.key === 'Enter' && search()} />
        <button className="btn-primary" onClick={search} disabled={loading}>{loading ? '搜索中...' : '搜索'}</button>
      </div>
      <div className="img-grid">
        {images.map(img => (
          <div key={img.id} className="img-card" onClick={() => copyUrl(img)} title="点击复制 Markdown">
            <img src={img.thumb} alt={img.alt} loading="lazy" />
            <div className="img-author">{img.author}</div>
          </div>
        ))}
      </div>
    </div>
  )
}
