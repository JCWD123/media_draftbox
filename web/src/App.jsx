import { useCallback, useMemo, useRef, useState } from 'react'
import { AppContext } from './utils/AppContext'
import AppRouter from './router'
import Toast from './components/common/Toast'
import { saveDraft as saveDraftApi } from './service/api/drafts'

/**
 * 应用根：持有全局共享状态（markdown + toast + 草稿操作）
 * 通过 AppContext 提供给所有页面（对齐 fusheng_ai 的全局状态管理思想）
 */
export default function App() {
  const [markdown, setMarkdown] = useState('# 标题\n\n这是测试内容')
  const [html, setHtml] = useState('') // 当前 wewrite 排版结果
  const [toast, setToast] = useState(null)
  // 自定义搜索结果的全局状态（切 Tab 后保留，直到下次搜索才更新）
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState([])
  const [searching, setSearching] = useState(false)
  const [selectedNews, setSelectedNews] = useState(new Set()) // 勾选的新闻素材（全局保留）
  const toastTimer = useRef(null)

  // 全局 toast（自动 3s 消失）
  const showToast = useCallback((type, message) => {
    setToast({ type, message, key: Date.now() })
    if (toastTimer.current) clearTimeout(toastTimer.current)
    toastTimer.current = setTimeout(() => setToast(null), 3000)
  }, [])

  // AI 结果保存为草稿（markdown 源 + wewrite HTML）
  const saveAsDraft = useCallback(async (title, content, html = '') => {
    await saveDraftApi(title, content, html)
    showToast('success', `✅ 已保存草稿: ${title}`)
  }, [showToast])

  const contextValue = useMemo(() => ({
    markdown, setMarkdown, html, setHtml, showToast, saveAsDraft,
    searchQuery, setSearchQuery, searchResults, setSearchResults, searching, setSearching,
    selectedNews, setSelectedNews,
  }), [markdown, html, showToast, saveAsDraft, searchQuery, searchResults, searching, selectedNews])

  return (
    <AppContext.Provider value={contextValue}>
      <AppRouter />
      {toast && (
        <div className="toast-container" key={toast.key}>
          <Toast type={toast.type} message={toast.message} onClose={() => setToast(null)} />
        </div>
      )}
    </AppContext.Provider>
  )
}
