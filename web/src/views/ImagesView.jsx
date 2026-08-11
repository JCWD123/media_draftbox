import { useState } from 'react'
import Button from '../components/common/Button'
import { DEFAULT_IMAGES } from '../utils/constants'
import { searchImages } from '../service/api/images'
import { useApp } from '../utils/AppContext'

/**
 * 图片搜索页
 */
export default function ImagesView() {
  const { showToast } = useApp()
  const [query, setQuery] = useState('')
  const [images, setImages] = useState(DEFAULT_IMAGES)
  const [loading, setLoading] = useState(false)

  const search = async () => {
    if (!query.trim()) { showToast('warn', '请输入搜索词'); return }
    setLoading(true)
    try {
      const d = await searchImages(query.trim(), 12)
      setImages(d.images || [])
    } catch { setImages([]) }
    setLoading(false)
  }

  const copyUrl = async (img) => {
    try {
      await navigator.clipboard.writeText(`![${img.alt}](${img.url})`)
      showToast('success', '✅ 已复制图片 Markdown')
    } catch (e) {
      showToast('error', `复制失败: ${e.message}`)
    }
  }

  return (
    <div className="panel full">
      <h2>🖼️ 图片搜索</h2>
      <div className="toolbar">
        <input value={query} onChange={e => setQuery(e.target.value)} placeholder="搜索图片..."
          onKeyDown={e => e.key === 'Enter' && search()} />
        <Button variant="primary" onClick={search} loading={loading}>
          {loading ? '搜索中' : '搜索'}
        </Button>
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
