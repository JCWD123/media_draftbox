import { memo } from 'react'
import NewsCheckItem from './NewsCheckItem'

/**
 * 新闻素材勾选面板（类别tab + 列表 + 已选计数）
 */
const NewsPicker = memo(({
  categories, activeCategory, onCategoryChange,
  news, selectedIds, onToggle, onClear,
}) => {
  return (
    <div className="news-select">
      <div className="news-select-header">
        <h3>📰 新闻素材勾选（可选，最多 10 条）</h3>
        <div className="news-cat-tabs">
          {categories.map(c => (
            <button
              key={c.id}
              className={`cat-tab ${activeCategory === c.id ? 'active' : ''}`}
              onClick={() => onCategoryChange(c.id)}
            >
              {c.name}
            </button>
          ))}
        </div>
        <span className="selected-count">
          已选 {selectedIds.size} 条
          {selectedIds.size > 0 && (
            <button className="link-btn" onClick={onClear}>清空</button>
          )}
        </span>
      </div>
      <div className="news-select-list">
        {news.map(item => (
          <NewsCheckItem
            key={item.id}
            item={item}
            checked={selectedIds.has(item.id)}
            onToggle={() => onToggle(item.id)}
          />
        ))}
        {news.length === 0 && <div className="news-empty">点击上方分类加载新闻</div>}
      </div>
    </div>
  )
})

export default NewsPicker
