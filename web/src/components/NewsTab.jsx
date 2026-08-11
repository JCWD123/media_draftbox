import { useState, useEffect } from 'react'
import { api, CATEGORY_COLORS } from '../lib/shared'

export default function NewsTab() {
  const [categories, setCategories] = useState([])
  const [category, setCategory] = useState('TECH')
  const [news, setNews] = useState([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    api('/news/categories').then(d => {
      const cats = (d.data || []).map(c => ({ id: c.category_code, name: c.category_name, icon: c.icon, color: c.color }))
      setCategories(cats)
    }).catch(() => {})
  }, [])

  const loadNews = async (cat) => {
    setCategory(cat); setLoading(true)
    try {
      const d = await api('/news/list', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ category: cat, page: 1, page_size: 20 })
      })
      setNews(d.news || [])
    } catch (e) { setNews([]) }
    setLoading(false)
  }

  useEffect(() => { loadNews(category) }, []) // 初始加载

  const currentName = categories.find(c => c.id === category)?.name || '热点新闻'

  return (
    <div className="news-layout">
      <aside className="news-sidebar">
        <h3>新闻分类</h3>
        {categories.map(c => (
          <div key={c.id} className={`news-cat-item ${category === c.id ? 'active' : ''}`}
            onClick={() => loadNews(c.id)}>
            <span className="cat-dot" style={{ background: c.color || '#999' }}></span>
            <span>{c.name}</span>
          </div>
        ))}
      </aside>
      <div className="news-main">
        <div className="news-header">
          <h2>{currentName}</h2>
          <span className="news-count">{news.length} 条新闻</span>
        </div>
        {loading ? (
          <div className="news-loading">加载中...</div>
        ) : (
          <div className="news-list">
            {news.map((item, i) => (
              <a key={item.id || i} className="news-card" href={item.link} target="_blank" rel="noopener noreferrer">
                <div className="news-card-title">{item.title}</div>
                <div className="news-card-meta">
                  <span className="news-source-badge" style={{ background: CATEGORY_COLORS[category] || '#999' }}>
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
  )
}
