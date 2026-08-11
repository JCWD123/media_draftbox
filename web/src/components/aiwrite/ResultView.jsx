import { memo } from 'react'
import Button from '../common/Button'
import { md } from '../../utils/constants'
import { sanitizePreviewHtml } from '../../utils/sanitizePreview'

/**
 * AI 生成结果视图
 * - html: 后端渲染好的完整 HTML（用 sanitizePreviewHtml 隔离 body 选择器后显示）
 * - markdown: 原始 MD（当无 html 时用 md 渲染）
 */
const ResultView = memo(({ title, markdown, html, onOpenConvert, onSaveDraft }) => {
  if (!markdown) return null
  const displayHtml = html ? sanitizePreviewHtml(html, { widen: true }) : md.render(markdown)
  return (
    <div className="ai-result">
      <div className="panel-head"><h3>{title}</h3></div>
      <div className="toolbar">
        <Button variant="primary" onClick={onOpenConvert}>📐 转为排版</Button>
        <Button variant="default" onClick={onSaveDraft}>💾 保存草稿</Button>
      </div>
      <div className="preview" style={{ minHeight: 520 }} dangerouslySetInnerHTML={{ __html: displayHtml }} />
    </div>
  )
})

export default ResultView
