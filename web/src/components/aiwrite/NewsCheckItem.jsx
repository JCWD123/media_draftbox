import { memo, useState } from 'react'
import { summarizeNews } from '../../service/api/news'

/**
 * 单条新闻勾选项
 * - 整行点击（label）触发勾选
 * - 右侧"查看原文"按钮：新标签打开原文
 * - "AI摘要"按钮：不点开原文，AI 概括这篇新闻大致讲了什么（展开显示）
 */
const NewsCheckItem = memo(({ item, checked, onToggle }) => {
  const inputId = `news-${item.id}`
  const title = item.title || ''
  const [summarizing, setSummarizing] = useState(false)
  const [aiSummary, setAiSummary] = useState('')
  const [showSummary, setShowSummary] = useState(false)
  const [summaryErr, setSummaryErr] = useState('')

  const handleSummarize = async (e) => {
    e.preventDefault()
    e.stopPropagation()
    // 已展开则收起
    if (showSummary) { setShowSummary(false); return }
    // 尚无摘要，触发生成
    if (!aiSummary && !summarizing) {
      setSummarizing(true)
      setSummaryErr('')
      try {
        const res = await summarizeNews(title, item.summary || '', item.link || '')
        if (res.success) setAiSummary(res.summary)
        else setSummaryErr(res.error || '生成失败')
      } catch (err) {
        setSummaryErr(`摘要失败: ${err.message}`)
      } finally {
        setSummarizing(false)
      }
    }
    setShowSummary(true)
  }

  return (
    <div className="news-check-wrap">
      <label className={`news-check-item ${checked ? 'checked' : ''}`} htmlFor={inputId}>
        <input id={inputId} type="checkbox" checked={checked} onChange={onToggle} />
        <span className="news-check-title">{title}</span>
        <span className="news-check-source">{item.source}</span>
        <button
          className="news-ai-summary-btn"
          onClick={handleSummarize}
          title="AI 摘要：不点开原文了解大致内容"
          disabled={summarizing}
        >
          {summarizing ? '⏳' : showSummary ? '▲' : '🤖摘要'}
        </button>
        {item.link && (
          <a
            className="news-check-link"
            href={item.link}
            target="_blank"
            rel="noopener noreferrer"
            title="查看原文"
            onClick={e => { e.preventDefault(); e.stopPropagation(); window.open(item.link, '_blank', 'noopener') }}
          >
            原文 ↗
          </a>
        )}
      </label>
      {showSummary && (
        <div className="news-ai-summary">
          {summarizing ? (
            <span className="summary-loading">⏳ AI 正在提炼这篇新闻的核心要点…</span>
          ) : aiSummary ? (
            <span className="summary-text">💡 {aiSummary}</span>
          ) : summaryErr ? (
            <span className="summary-err">⚠ {summaryErr}</span>
          ) : null}
        </div>
      )}
    </div>
  )
})

export default NewsCheckItem
