import { memo } from 'react'

/**
 * 标签栏 + 垂直度提示
 */
const TagBar = memo(({ tags, vertical }) => {
  if (tags.length === 0 && !vertical) return null
  return (
    <div className="tag-bar">
      {tags.map(t => <span key={t} className="tag">#{t}</span>)}
      {vertical && <span className="vertical-note">{vertical}</span>}
    </div>
  )
})

export default TagBar
