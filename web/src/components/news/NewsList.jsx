import { memo } from 'react'
import NewsCard from './NewsCard'
import Loading from '../common/Loading'

/**
 * 新闻列表（含空态/加载态）
 */
const NewsList = memo(({ news, category, loading }) => {
  if (loading) return <Loading text="加载中..." minHeight={200} />
  return (
    <div className="news-list">
      {news.map((item, i) => (
        <NewsCard key={item.id || i} item={item} category={category} />
      ))}
      {news.length === 0 && <div className="news-empty">暂无新闻</div>}
    </div>
  )
})

export default NewsList
