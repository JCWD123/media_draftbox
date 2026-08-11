import { createContext, useContext } from 'react'

/**
 * 全局共享状态（类似 fusheng_ai 的 redux，但用轻量 Context）
 * - markdown: 当前编辑器内容（排版/草稿共用）
 * - html: 当前 wewrite 排版结果（预览共用）
 * - toast: 全局通知
 */
export const AppContext = createContext(null)

// 在组件内读取共享状态
export function useApp() {
  const ctx = useContext(AppContext)
  if (!ctx) throw new Error('useApp 必须在 AppProvider 内使用')
  return ctx
}
