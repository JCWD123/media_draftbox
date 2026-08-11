import { memo } from 'react'

/**
 * 新闻分类侧边栏
 */
const CategorySidebar = memo(({ categories, activeId, onSelect }) => {
  return (
    <aside className="news-sidebar">
      <h3>新闻分类</h3>
      {categories.map(c => (
        <div
          key={c.id}
          className={`news-cat-item ${activeId === c.id ? 'active' : ''}`}
          onClick={() => onSelect(c.id)}
        >
          <span className="cat-dot" style={{ background: c.color || '#999' }} />
          <span>{c.name}</span>
        </div>
      ))}
    </aside>
  )
})

export default CategorySidebar
