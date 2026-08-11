import { useState, useEffect } from 'react'
import CategorySidebar from '../components/news/CategorySidebar'
import NewsList from '../components/news/NewsList'
import { getCategories } from '../service/api/news'
import { getCachedNews, prefetchNews } from '../utils/newsCache'

/**
 * 热点新闻页
 */
export default function NewsView({ }) {
  const [categories, setCategories] = useState([])
  const [category, setCategory] = useState('TECH')
  const [news, setNews] = useState([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    getCategories().then(d => {
      const cats = (d.data || []).map(c => ({
        id: c.category_code, name: c.category_name, icon: c.icon, color: c.color
      }))
      setCategories(cats)
    }).catch(() => {})
  }, [])

  const loadNews = async (cat) => {
    setCategory(cat)
    setLoading(true)
    try {
      const { news } = await getCachedNews(cat)
      setNews(news)
    } catch { setNews([]) }
    setLoading(false) // 数据到手后必关 loading（无论缓存命中与否）
  }

  useEffect(() => { loadNews('TECH') }, [])

  const currentName = categories.find(c => c.id === category)?.name || '热点新闻'

  return (
    <div className="news-layout">
      <CategorySidebar categories={categories} activeId={category} onSelect={loadNews} />
      <div className="news-main">
        <div className="news-header">
          <h2>{currentName}</h2>
          <span className="news-count">{news.length} 条新闻</span>
        </div>
        <NewsList news={news} category={category} loading={loading} />
      </div>
    </div>
  )
}
