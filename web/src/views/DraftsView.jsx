import { useState, useEffect } from 'react'
import Button from '../components/common/Button'
import { listDrafts, getDraft, saveDraft, deleteDraft } from '../service/api/drafts'
import { sanitizePreviewHtml } from '../utils/sanitizePreview'
import { useApp } from '../utils/AppContext'

// 从 markdown 或 html 自动提取标题
function extractTitle(markdown, html) {
  // 1. markdown 首个 # 标题
  const mdMatch = (markdown || '').match(/^#\s+(.+)$/m)
  if (mdMatch) return mdMatch[1].trim().slice(0, 50)
  // 2. html 的 title 标签
  const htmlTitle = (html || '').match(/<title[^>]*>([^<]+)<\/title>/i)
  if (htmlTitle) return htmlTitle[1].trim().slice(0, 50)
  // 3. 默认
  return `未命名草稿 ${new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}`
}

/**
 * 草稿管理页
 * - 列表 + 点击后在内嵌预览区展示该草稿的 HTML（排版结果）
 * - 保存草稿：无需输入标题，自动从内容提取标题，存 markdown 源 + wewrite HTML
 */
export default function DraftsView() {
  const { markdown, html, setMarkdown, setHtml, showToast } = useApp()
  const [drafts, setDrafts] = useState([])
  const [previewHtml, setPreviewHtml] = useState('') // 当前查看的草稿 html
  const [previewMeta, setPreviewMeta] = useState('') // 当前查看的草稿标题

  const refresh = async () => {
    try {
      const d = await listDrafts()
      setDrafts(d.drafts || [])
    } catch {}
  }
  useEffect(() => { refresh() }, [])

  const save = async () => {
    if (!markdown && !html) {
      showToast('warn', '当前没有可保存的内容')
      return
    }
    const autoTitle = extractTitle(markdown, html)
    await saveDraft(autoTitle, markdown || '', html || '')
    refresh()
    showToast('success', '✅ 已保存草稿')
  }

  const load = async (filename, dTitle) => {
    try {
      const d = await getDraft(filename)
      setMarkdown(d.markdown || '')
      setHtml(d.html || '')
      setPreviewHtml(d.html || '')
      setPreviewMeta(dTitle)
      if (d.html) {
        // 已有 html 直接展示
      } else {
        showToast('info', `该草稿暂无 HTML，可到排版页生成`)
      }
    } catch (e) { showToast('error', `加载失败: ${e.message}`) }
  }

  const remove = async (e, filename) => {
    e.stopPropagation()
    if (!window.confirm('确定删除该草稿？')) return
    await deleteDraft(filename)
    if (previewMeta && drafts.some(d => d.filename === filename)) {
      // 若删除的是当前预览的草稿，清空预览
      if (drafts.find(d => d.filename === filename)?.title === previewMeta) {
        setPreviewHtml(''); setPreviewMeta('')
      }
    }
    refresh()
  }

  return (
    <div className="drafts-layout">
      {/* 左侧：草稿列表 */}
      <div className="panel full drafts-side">
        <div className="panel-head">
          <h2>📄 草稿管理</h2>
          <Button variant="primary" onClick={save}>➕ 保存当前内容</Button>
        </div>
        <div className="draft-list">
          {drafts.map(d => (
            <div
              key={d.filename}
              className={`draft-item ${previewMeta === d.title ? 'active' : ''}`}
              onClick={() => load(d.filename, d.title)}
            >
              <span className="draft-title">{d.title}</span>
              <span className="draft-time">{d.updated_at?.slice(5, 16) || ''}</span>
              <button className="draft-delete" onClick={e => remove(e, d.filename)} title="删除">🗑</button>
            </div>
          ))}
          {drafts.length === 0 && <div className="news-empty">暂无草稿</div>}
        </div>
      </div>

      {/* 右侧：HTML 预览 */}
      <div className="panel full drafts-preview">
        <div className="panel-head">
          <h2>草稿预览</h2>
          {previewMeta && <span className="muted">{previewMeta}</span>}
        </div>
        {previewHtml ? (
          <div className="preview" dangerouslySetInnerHTML={{ __html: sanitizePreviewHtml(previewHtml, { widen: true }) }} />
        ) : (
          <div className="news-empty">
            {previewMeta ? `${previewMeta} 暂无 HTML 预览，请到排版页生成或保存时带 HTML` : '点击左侧草稿查看排版预览'}
          </div>
        )}
      </div>
    </div>
  )
}
