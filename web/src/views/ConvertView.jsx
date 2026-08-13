import { useState, useEffect, useRef } from 'react'
import Button from '../components/common/Button'
import ThemeSelector from '../components/convert/ThemeSelector'
import { ListDraftsPanel } from '../components/drafts/DraftSelector'
import { convertMarkdown } from '../service/api/convert'
import { getDraft } from '../service/api/drafts'
import { illustrateArticle } from '../service/api/illustrate'
import { sanitizePreviewHtml } from '../utils/sanitizePreview'
import { useApp } from '../utils/AppContext'

/**
 * 从后端 warning 文本里提炼可读的原因（识别常见错误，给可操作提示）
 */
function shortError(warning) {
  if (!warning) return ''
  const w = String(warning)
  if (/AccountOverdue|overdue balance|欠费/i.test(w)) return '图片服务账户欠费，请充值后重试'
  if (/403|Forbidden/i.test(w)) return '图片服务拒绝请求(403)，可能是账户欠费或权限问题'
  if (/401|Unauthorized|api key|key错误|鉴权/i.test(w)) return '图片服务 API Key 无效，请检查配置'
  if (/429|rate limit|限流/i.test(w)) return '图片服务限流，请稍后重试'
  if (/timeout|超时/i.test(w)) return '图片生成超时，请重试'
  // 兜底：截取错误里的 code/message 关键片段
  const codeMatch = w.match(/code["']?\s*[:：]\s*["']?(\w+)/i)
  if (codeMatch) return `图片服务错误: ${codeMatch[1]}`
  return w.slice(0, 80)
}

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
  const [materialName, setMaterialName] = useState('') // 已上传的物料.md 文件名
  const [materialMd, setMaterialMd] = useState('') // 物料.md 内容
  const [illustrating, setIllustrating] = useState(false) // 配图中
  const fileInputRef = useRef(null)

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

  // 从草稿加载某篇文章并渲染
  const loadFromDraft = async (filename) => {
    try {
      const d = await getDraft(filename)
      setCurrentSource(d.title || filename)
      if (d.markdown) setMarkdown(d.markdown)
      if (d.html && d.html.trim()) {
        // 有保存的 HTML：优先展示（与草稿预览一致，避免 wewrite 重新转换导致变样）
        setRecentHtml(d.html); setHtml(d.html)
        showToast('success', `已加载草稿: ${d.title}`)
      } else if (d.markdown) {
        // 仅 markdown：用当前主题重新转换
        const result = await renderWithTheme(d.markdown, theme)
        if (result) { setRecentHtml(result); setHtml(result) }
        showToast('success', `已加载草稿: ${d.title}`)
      } else {
        showToast('info', '该草稿无内容')
      }
    } catch (e) { showToast('error', `加载失败: ${e.message}`) }
  }

  // 初始：若已有 html（AI 生成）直接展示
  useEffect(() => {
    if (html && !recentHtml) setRecentHtml(html)
  }, [html])

  // 读取物料.md 文件（纯前端读文本，不调用后端）
  const handleMaterialFile = (e) => {
    const file = e.target.files && e.target.files[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = () => {
      setMaterialMd(String(reader.result || ''))
      setMaterialName(file.name)
      showToast('success', `已加载物料: ${file.name}`)
    }
    reader.onerror = () => showToast('error', '读取物料文件失败')
    reader.readAsText(file, 'utf-8')
  }

  // 按物料给当前 HTML 配图
  const handleIllustrate = async () => {
    if (!recentHtml || !recentHtml.trim()) { showToast('warn', '请先选择文章生成排版'); return }
    if (!materialMd || !materialMd.trim()) { showToast('warn', '请先上传发布物料.md 文件'); return }
    setIllustrating(true)
    try {
      const res = await illustrateArticle(recentHtml, materialMd)
      if (!res.success) {
        showToast('error', `配图失败: ${res.error || '未知错误'}`)
        return
      }

      const inserted = (res.inserted || []).filter(i => i.ok)
      const warnings = res.warnings || []
      const nOk = inserted.length
      const nFail = warnings.length

      // 三态结果：全成功 / 部分成功 / 全失败
      if (nOk > 0 && nFail === 0) {
        // 全部成功
        setRecentHtml(res.html); setHtml(res.html)
        showToast('success', `✅ 已插入 ${nOk} 张图片`)
      } else if (nOk > 0 && nFail > 0) {
        // 部分成功
        setRecentHtml(res.html); setHtml(res.html)
        showToast('warn', `⚠️ 成功 ${nOk} 张，失败 ${nFail} 张`)
        const reason = shortError(warnings[0])
        if (reason) showToast('info', `失败原因: ${reason}`)
      } else {
        // 全部失败（nOk === 0）
        const reason = shortError(warnings[0])
        showToast('error', reason ? `❌ 配图失败: ${reason}` : '❌ 配图失败，图片生成失败')
        // 不改动 html，保持原预览
      }
    } catch (e) {
      showToast('error', `配图失败: ${e.message}`)
    } finally {
      setIllustrating(false)
    }
  }


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

        {/* 配图区块：上传发布物料.md → 按物料规则给当前文章插图 */}
        <div className="illustrate-panel">
          <h4>📷 按物料配图</h4>
          <input
            ref={fileInputRef}
            type="file"
            accept=".md,.markdown,.txt"
            style={{ display: 'none' }}
            onChange={handleMaterialFile}
          />
          <div className="illustrate-row">
            <Button variant="default" size="sm" onClick={() => fileInputRef.current && fileInputRef.current.click()}>
              📄 上传物料.md
            </Button>
            <Button variant="primary" size="sm" loading={illustrating} onClick={handleIllustrate}>
              🎨 生成配图
            </Button>
          </div>
          <div className="muted illustrate-meta">
            {materialName ? `已加载: ${materialName}` : '上传「发布物料.md」后生成配图并插入'}
          </div>
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
          <div className="preview" dangerouslySetInnerHTML={{ __html: sanitizePreviewHtml(recentHtml, { widen: false }) }} />
        ) : (
          <div className="news-empty">
            {markdown ? '请选择左侧草稿或切换主题生成排版' : '请从左侧选择一篇草稿，或用 AI 写作生成文章'}
          </div>
        )}
      </div>
    </div>
  )
}
