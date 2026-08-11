import { memo } from 'react'

/**
 * 卡片容器
 * title: 标题
 * extra: 右上角额外元素
 * full: 是否撑满宽度
 */
const Panel = memo(({ title, extra, children, full = false, className = '', headIcon }) => {
  const cls = ['panel', full ? 'full' : '', className].filter(Boolean).join(' ')
  return (
    <section className={cls}>
      {(title || extra) && (
        <div className="panel-head">
          <h2>{headIcon}{title}</h2>
          {extra}
        </div>
      )}
      {children}
    </section>
  )
})

export default Panel
