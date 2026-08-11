import { NavLink } from 'react-router-dom'
import { TABS } from '../../utils/constants'

/**
 * 顶部 Tab 导航
 */
function TabNav() {
  return (
    <nav className="nav">
      {TABS.map(t => (
        <NavLink
          key={t.id}
          to={t.path}
          end={t.path === '/'}
          className={({ isActive }) => `nav-btn ${isActive ? 'active' : ''}`}
        >
          <span className="nav-icon">{t.icon}</span>
          <span className="nav-label">{t.label}</span>
        </NavLink>
      ))}
    </nav>
  )
}

export default TabNav
