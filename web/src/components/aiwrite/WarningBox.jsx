import { memo } from 'react'

/**
 * 警告/错误提示框（多条）
 */
const WarningBox = memo(({ warnings }) => {
  if (!warnings || warnings.length === 0) return null
  return (
    <div className="warnings">
      {warnings.map((w, i) => <div key={i}>⚠ {w}</div>)}
    </div>
  )
})

export default WarningBox
