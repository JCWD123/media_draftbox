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
  }), [markdown, html, showToast, saveAsDraft])

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
