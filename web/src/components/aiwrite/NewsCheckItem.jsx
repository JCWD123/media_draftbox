import { memo, useState, useEffect, useRef } from 'react'
import { summarizeNews } from '../../service/api/news'
import { peekSummary, setSummary, subscribeSummary } from '../../utils/newsSummaryCache'

/**
 * 单条新闻勾选项
 * - 整行点击（label）触发勾选
 * - 右侧"查看原文"按钮：新标签打开原文
 * - "AI摘要"按钮：不点开原文，AI 概括这篇新闻大致讲了什么（展开显示）
 * - 摘要缓存到全局 newsSummaryCache，切换页面/类别后不丢失
 */
const NewsCheckItem = memo(({ item, checked, onToggle }) => {
  const inputId = `news-${item.id}`
  const title = item.title || ''
  const cached = useRef(peekSummary(item.id) || null) // 挂载时从缓存读

  const [summarizing, setSummarizing] = useState(false)
  const [aiSummary, setAiSummary] = useState(cached.current?.summary || '')
  const [showSummary, setShowSummary] = useState(!!cached.current) // 有缓存默认展开
  const [summaryErr, setSummaryErr] = useState(cached.current?.err || '')

  // 订阅全局缓存变化：别处生成/更新了本条摘要时同步到本组件
  useEffect(() => {
    const unsub = subscribeSummary(() => {
      const cur = peekSummary(item.id)
      if (cur) {
        setAiSummary(cur.summary || '')
        setSummaryErr(cur.err || '')
        setSummarizing(false)
      }
    })
    return unsub
  }, [item.id])

  const handleSummarize = async (e) => {
    e.preventDefault()
    e.stopPropagation()
    // 已展开则收起
    if (showSummary) { setShowSummary(false); return }
    // 尚无摘要，触发生成
    if (aiSummary === '' && !summarizing) {
      setSummarizing(true)
      setSummaryErr('')
      try {
        const res = await summarizeNews(title, item.summary || '', item.link || '')
        if (res.success) {
          setAiSummary(res.summary)
          // 写入全局缓存
          setSummary(item.id, { summary: res.summary, err: '' })
        } else {
          setSummaryErr(res.error || '生成失败')
          setSummary(item.id, { summary: '', err: res.error || '生成失败' })
        }
      } catch (err) {
        setSummaryErr(`摘要失败: ${err.message}`)
        setSummary(item.id, { summary: '', err: `摘要失败: ${err.message}` })
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
          {summarizing ? '⏳' : showSummary ? '▲' : (aiSummary || summaryErr) ? '🤖摘要' : '🤖摘要'}
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
