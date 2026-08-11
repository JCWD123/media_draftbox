import { Outlet } from 'react-router-dom'
import Header from './Header'
import TabNav from './TabNav'

/**
 * 全站布局：头部 + Tab 导航 + 内容出口
 */
function Layout() {
  return (
    <div className="app">
      <Header />
      <TabNav />
      <main className="main">
        <Outlet />
      </main>
    </div>
  )
}

export default Layout
