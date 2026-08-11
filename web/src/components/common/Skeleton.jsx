import { memo } from 'react'

/**
 * 骨架屏（加载占位）
 */
const Skeleton = memo(({ rows = 3, className = '' }) => (
  <div className={`skeleton ${className}`}>
    {Array.from({ length: rows }).map((_, i) => (
      <div key={i} className="skeleton-line" style={{ width: `${100 - i * 15}%` }} />
    ))}
  </div>
))

export default Skeleton
