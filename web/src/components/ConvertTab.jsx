import { useMemo, useState } from 'react'
import { md, WECHAT_CSS, notify } from '../lib/shared'

const THEMES = [
  { id: 'professional', name: '专业简洁' },
  { id: 'minimal', name: '极简' },
  { id: 'github', name: 'GitHub风格' },
  { id: 'newspaper', name: '报纸风格' },
  { id: 'bold-navy', name: '深蓝粗体' },
]

export default function ConvertTab({ markdown, onMarkdownChange }) {
  const [theme, setTheme] = useState('professional')

  const html = useMemo(
    () => `<style>${WECHAT_CSS}</style><div>${md.render(markdown || '')}</div>`,
    [markdown]
  )

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.write([new ClipboardItem({ 'text/html': new Blob([html], { type: 'text/html' }) })])
      notify('✅ 已复制 HTML')
    } catch (e) {
      notify('复制失败: ' + e.message)
    }
  }

  return (
    <div className="split">
      <div className="panel editor-panel">
        <div className="panel-head">
          <h2>Markdown</h2>
          <span className="muted">{(markdown || '').length} 字</span>
        </div>
        <div className="toolbar">
          <select value={theme} onChange={e => setTheme(e.target.value)}>
            {THEMES.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
          </select>
          <button className="btn-primary" onClick={copyToClipboard}>📋 复制HTML</button>
        </div>
        <textarea
          className="code-editor"
          value={markdown}
          onChange={e => onMarkdownChange(e.target.value)}
          placeholder="# 在这里输入 Markdown..."
        />
      </div>
      <div className="panel preview-panel">
        <div className="panel-head">
          <h2>预览</h2>
        </div>
        <div className="preview" dangerouslySetInnerHTML={{ __html: html }} />
      </div>
    </div>
  )
}
