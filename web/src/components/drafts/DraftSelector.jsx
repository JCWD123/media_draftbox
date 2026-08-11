import { useState, useEffect, memo } from 'react'
import { listDrafts } from '../../service/api/drafts'

/**
 * 草稿选择面板（排版页左侧用）
 * 列出所有草稿，点击选择一篇用于排版测试
 */
const ListDraftsPanel = memo(({ onSelect }) => {
  const [drafts, setDrafts] = useState([])
  const [loaded, setLoaded] = useState('')

  useEffect(() => {
    listDrafts().then(d => setDrafts(d.drafts || [])).catch(() => {})
  }, [])

  return (
    <div className="draft-selector">
      <div className="draft-selector-head">
        <h4>📂 选择文章测试排版</h4>
        {drafts.length === 0 && <span className="muted">暂无草稿</span>}
      </div>
      <div className="draft-selector-list">
        {drafts.map(d => (
          <div
            key={d.filename}
            className={`draft-select-item ${loaded === d.filename ? 'active' : ''}`}
            onClick={() => { setLoaded(d.filename); onSelect(d.filename) }}
          >
            <span className="draft-title">{d.title}</span>
          </div>
        ))}
      </div>
    </div>
  )
})

export { ListDraftsPanel }
