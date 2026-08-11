import { memo } from 'react'
import { md, WECHAT_CSS } from '../../utils/constants'

/**
 * 预览面板
 * - html: 已 wewrite 排版的结果（优先显示，保持所见即所得）
 * - markdown: 源 md（当无 html 时用本地 md 渲染兜底）
 */
const PreviewPanel = memo(({ markdown, html = '', height = 480 }) => {
  // 有 wewrite html 就用它，否则本地 md 渲染
  const displayHtml = html
    ? html
    : `<style>${WECHAT_CSS}</style><div>${md.render(markdown || '')}</div>`

  return (
    <div className="panel preview-panel">
      <div className="panel-head"><h2>预览</h2></div>
      <div className="preview" style={{ minHeight: height }} dangerouslySetInnerHTML={{ __html: displayHtml }} />
    </div>
  )
})

export default PreviewPanel
