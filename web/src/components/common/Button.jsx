import { memo } from 'react'

/**
 * 通用按钮
 * variant: primary | default | ghost | danger
 */const Button = memo(({
  children,
  onClick,
  variant = 'default',
  size = 'md',
  loading = false,
  disabled = false,
  type = 'button',
  className = '',
  ...rest
}) => {
  const cls = ['btn', `btn-${variant}`, `btn-${size}`, loading ? 'is-loading' : '', className]
    .filter(Boolean).join(' ')
  return (
    <button
      type={type}
      className={cls}
      onClick={onClick}
      disabled={disabled || loading}
      {...rest}
    >
      {loading && <span className="btn-spinner" />}
      {children}
    </button>
  )
})

export default Button
