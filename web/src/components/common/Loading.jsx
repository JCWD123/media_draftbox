import { memo } from 'react'

/**
 * 加载态
 * text: 加载文案
 * minHeight: 最小高度
 */
const Loading = memo(({ text = '加载中...', minHeight = 120 }) => (
  <div className="loading" style={{ minHeight }}>
    <span className="loading-spinner" />
    <span className="loading-text">{text}</span>
  </div>
))

export default Loading
