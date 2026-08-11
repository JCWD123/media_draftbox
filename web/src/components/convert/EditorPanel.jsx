import { memo } from 'react'

/**
 * Markdown 编辑器面板
 */
const EditorPanel = memo(({ markdown, onChange }) => {
  const charCount = (markdown || '').length
  return (
    <div className="panel editor-panel">
      <div className="panel-head">
        <h2>Markdown</h2>
        <span className="muted">{charCount} 字</span>
      </div>
      <textarea
        className="code-editor"
        value={markdown}
        onChange={e => onChange(e.target.value)}
        placeholder="# 在这里输入 Markdown..."
        spellCheck={false}
      />
    </div>
  )
})

export default EditorPanel
