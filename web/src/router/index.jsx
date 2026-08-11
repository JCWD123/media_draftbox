import { lazy, Suspense } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from '../components/layout'
import Loading from '../components/common/Loading'

// 懒加载页面（对齐 fusheng_ai 的 Lazy 模式）
const ConvertView = lazy(() => import('../views/ConvertView'))
const NewsView = lazy(() => import('../views/NewsView'))
const AiWriteView = lazy(() => import('../views/AiWriteView'))
const ImagesView = lazy(() => import('../views/ImagesView'))
const DraftsView = lazy(() => import('../views/DraftsView'))

const withSuspense = (el) => <Suspense fallback={<Loading />}>{el}</Suspense>

/**
 * 声明式路由（BrowserRouter + Routes）
 */
export default function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={withSuspense(<ConvertView />)} />
          <Route path="news" element={withSuspense(<NewsView />)} />
          <Route path="ai" element={withSuspense(<AiWriteView />)} />
          <Route path="images" element={withSuspense(<ImagesView />)} />
          <Route path="drafts" element={withSuspense(<DraftsView />)} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
