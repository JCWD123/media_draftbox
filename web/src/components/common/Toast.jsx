import { memo } from 'react'

/**
 * 轻量 Toast 通知
 * 用法: <Toast type="success|error|warn|info" message="..." onClose={fn} />
 */
const Toast = memo(({ type = 'info', message, onClose }) => {
  const icons = { success: '✅', error: '❌', warn: '⚠️', info: 'ℹ️' }
  return (
    <div className={`toast toast-${type}`} onClick={onClose}>
      <span className="toast-icon">{icons[type]}</span>
      <span className="toast-msg">{message}</span>
    </div>
  )
})

export default Toast
