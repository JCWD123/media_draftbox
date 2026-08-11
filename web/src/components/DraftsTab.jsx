import { useState, useEffect } from 'react'
import { api, notify } from '../lib/shared'

export default function DraftsTab({ markdown, onLoadContent }) {
  const [drafts, setDrafts] = useState([])
  const [title, setTitle] = useState('')

  const refresh = () => {
    api('/drafts').then(d => setDrafts(d.drafts || [])).catch(() => {})
  }
  useEffect(() => { refresh() }, [])

  const save = async () => {
    if (!title.trim()) { notify('请输入草稿标题'); return }
    await api('/drafts', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: title.trim(), content: markdown || '' })
    })
    setTitle('')
    refresh()
    notify('✅ 已保存草稿')
  }

  const load = async (filename) => {
    try {
      const d = await api(`/drafts/${filename}`)
      onLoadContent(d.content)
    } catch (e) { notify('加载失败: ' + e.message) }
  }

  const remove = async (e, filename) => {
    e.stopPropagation()
    if (!window.confirm('确定删除该草稿？')) return
    await api(`/drafts/${filename}`, { method: 'DELETE' })
    refresh()
  }

  return (
    <div className="panel full">
      <h2>📄 草稿管理</h2>
      <div className="toolbar">
        <input value={title} onChange={e => setTitle(e.target.value)} placeholder="草稿标题..." />
        <button className="btn-primary" onClick={save}>保存</button>
      </div>
      <div className="draft-list">
        {drafts.map(d => (
          <div key={d.filename} className="draft-item" onClick={() => load(d.filename)}>
            <span className="draft-title">{d.title}</span>
            <button className="draft-delete" onClick={e => remove(e, d.filename)} title="删除">🗑</button>
          </div>
        ))}
        {drafts.length === 0 && <div className="news-empty">暂无草稿</div>}
      </div>
    </div>
  )
}
