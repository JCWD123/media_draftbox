import { memo } from 'react'

/**
 * 单条新闻勾选项
 * - 整行点击（label）触发勾选
 * - 右侧"查看原文"按钮：新标签打开原文链接，不触发勾选
 */
const NewsCheckItem = memo(({ item, checked, onToggle }) => {
  const inputId = `news-${item.id}`
  return (
    <label className={`news-check-item ${checked ? 'checked' : ''}`} htmlFor={inputId}>
      <input id={inputId} type="checkbox" checked={checked} onChange={onToggle} />
      <span className="news-check-title">{item.title}</span>
      <span className="news-check-source">{item.source}</span>
      {item.link && (
        <a
          className="news-check-link"
          href={item.link}
          target="_blank"
          rel="noopener noreferrer"
          title="查看原文"
          onClick={e => { e.preventDefault(); e.stopPropagation(); window.open(item.link, '_blank', 'noopener') }}
        >
          原文 ↗
        </a>
      )}
    </label>
  )
})

export default NewsCheckItem
