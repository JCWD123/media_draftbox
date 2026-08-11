import { useState, useEffect } from 'react'
import Button from '../components/common/Button'
import ThemeSelector from '../components/convert/ThemeSelector'
import { ListDraftsPanel } from '../components/drafts/DraftSelector'
import { convertMarkdown } from '../service/api/convert'
import { getDraft } from '../service/api/drafts'
import { useApp } from '../utils/AppContext'

/**
 * 排版转换页
 * - 左侧：草稿选择（加载某篇草稿的 markdown） + 主题切换 + 复制
 * - 右侧：wewrite 排版预览（随主题切换实时重新渲染）
 */
export default function ConvertView() {
  const { markdown, setMarkdown, html, setHtml, showToast } = useApp()
  const [theme, setTheme] = useState('premium')
  const [converting, setConverting] = useState(false)
  const [recentHtml, setRecentHtml] = useState(html || '') // 当前预览的 html
  const [currentSource, setCurrentSource] = useState('最近生成') // 来源标记

  // 用当前 markdown 按指定主题走 wewrite 转换
  const renderWithTheme = async (md, th) => {
    if (!md || !md.trim()) {
      showToast('warn', '请先选择或输入文章内容')
      return null
    }
    setConverting(true)
    try {
      const res = await convertMarkdown(md, th)
      if (!res.html) { showToast('error', `转换失败: ${res.error || '未知错误'}`); return null }
      return res.html
    } catch (e) {
      showToast('error', `转换失败: ${e.message}`)
      return null
    } finally {
      setConverting(false)
    }
  }

  // 主题切换 → 重新 wewrite 渲染
  const handleThemeChange = async (newTheme) => {
    setTheme(newTheme)
    const result = await renderWithTheme(markdown, newTheme)
    if (result) { setRecentHtml(result); setHtml(result) }
  }

  // 复制当前预览的 HTML
  const copyHtml = async () => {
    if (!recentHtml) { showToast('warn', '请先选择文章生成排版'); return }
    try {
      await navigator.clipboard.write([
        new ClipboardItem({ 'text/html': new Blob([recentHtml], { type: 'text/html' }) })
      ])
      showToast('success', '✅ 已复制微信兼容 HTML')
    } catch (e) { showToast('error', `复制失败: ${e.message}`) }
  }

  // 从草稿加载某篇文章的 markdown 并渲染
  const loadFromDraft = async (filename) => {
    try {
      const d = await getDraft(filename)
      if (d.markdown) {
        setMarkdown(d.markdown)
        setCurrentSource(d.title || filename)
        // 立即用当前主题渲染
        const result = await renderWithTheme(d.markdown, theme)
        if (result) { setRecentHtml(result); setHtml(result) }
        showToast('success', `已加载草稿: ${d.title}`)
      } else {
        // 无 markdown，只有 html，直接展示
        setRecentHtml(d.html || '')
        setHtml(d.html || '')
        setCurrentSource(d.title || filename)
        showToast('info', '该草稿只有 HTML，按原排版展示')
      }
    } catch (e) { showToast('error', `加载失败: ${e.message}`) }
  }

  // 初始：若已有 html（AI 生成）直接展示
  useEffect(() => {
    if (html && !recentHtml) setRecentHtml(html)
  }, [html])

  return (
    <div className="convert-layout">
      {/* 左侧控制面板 */}
      <div className="panel full convert-side">
        <div className="panel-head">
          <h2>排版转换</h2>
        </div>
        <div className="convert-toolbar">
          <ThemeSelector value={theme} onChange={handleThemeChange} />
          <Button variant="primary" onClick={copyHtml}>📋 复制HTML</Button>
        </div>
        <div className="convert-source">
          <span className="muted">当前来源: {currentSource}</span>
        </div>
        <ListDraftsPanel onSelect={loadFromDraft} />
      </div>

      {/* 右侧预览 */}
      <div className="panel full convert-preview">
        <div className="panel-head">
          <h2>排版预览</h2>
          <span className="muted">{currentSource}</span>
        </div>
        {recentHtml ? (
          <div className="preview" dangerouslySetInnerHTML={{ __html: recentHtml }} />
        ) : (
          <div className="news-empty">
            {markdown ? '请选择左侧草稿或切换主题生成排版' : '请从左侧选择一篇草稿，或用 AI 写作生成文章'}
          </div>
        )}
      </div>
    </div>
  )
}
