import { API } from '../lib/shared'

const TABS = [
  { id: 'convert', label: '📝 排版转换' },
  { id: 'news', label: '🔥 热点新闻' },
  { id: 'ai', label: '🤖 AI写作' },
  { id: 'images', label: '🖼️ 图片搜索' },
  { id: 'drafts', label: '📄 草稿管理' }
]

export default function Header({ tab, onTabChange }) {
  return (
    <>
      <header className="header">
        <div className="brand">
          <div className="brand-logo">✦</div>
          <h1>DraftBox</h1>
        </div>
        <span className="subtitle">会学习的 AI 写作助手（文字 + 图片 + 视频）</span>
      </header>
      <nav className="nav">
        {TABS.map(t => (
          <button
            key={t.id}
            className={tab === t.id ? 'nav-btn active' : 'nav-btn'}
            onClick={() => onTabChange(t.id)}
          >
            {t.label}
          </button>
        ))}
      </nav>
    </>
  )
}
