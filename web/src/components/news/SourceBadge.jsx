import { memo } from 'react'
import { CATEGORY_COLORS } from '../../utils/constants'

/**
 * 新闻来源徽标
 */
const SourceBadge = memo(({ source, category }) => (
  <span className="news-source-badge" style={{ background: CATEGORY_COLORS[category] || '#999' }}>
    {source}
  </span>
))

export default SourceBadge
