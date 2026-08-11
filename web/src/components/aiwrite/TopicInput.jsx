import { memo } from 'react'

/**
 * 话题输入框（必填）
 */
const TopicInput = memo(({ value, onChange, onEnter }) => (
  <input
    className="topic-input"
    value={value}
    onChange={e => onChange(e.target.value)}
    onKeyDown={e => e.key === 'Enter' && onEnter()}
    placeholder="输入话题/核心思路（必填）..."
    style={{ flex: 1 }}
  />
))

export default TopicInput
