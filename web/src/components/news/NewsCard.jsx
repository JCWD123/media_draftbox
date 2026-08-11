import { memo } from 'react'
import SourceBadge from './SourceBadge'

/**
 * 单条新闻卡片
 */
const NewsCard = memo(({ item, category }) => (
  <a className="news-card" href={item.link} target="_blank" rel="noopener noreferrer">
    <div className="news-card-title">{item.title}</div>
    <div className="news-card-meta">
      <SourceBadge source={item.source} category={category} />
      <span className="news-date">{item.published}</span>
    </div>
  </a>
))

export default NewsCard
