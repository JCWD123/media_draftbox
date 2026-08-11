/**
 * 分类新闻缓存（AI 写作素材栏 + 热点新闻页共用）
 * - 加载过的类别缓存，再次切换读缓存秒开，后台静默刷新
 * - TTL 默认 5 分钟过期后重新请求
 * - 并发去重：同一类别同时多个请求共用同一个 pending Promise
 */
import { getNewsList } from '../service/api/news'

const TTL = 5 * 60 * 1000 // 5 分钟缓存有效期

const store = new Map()      // categoryCode -> { news, ts }
const pending = new Map()    // categoryCode -> Promise（并发去重）

let listener = null

/** 设置缓存变化监听（供 UI 刷新） */
export function setNewsCacheListener(fn) {
  listener = fn
}

function emit() {
  if (listener) listener()
}

/**
 * 获取某分类新闻（优先缓存，缓存过期/未命中则请求）
 * 返回 { news, fromCache }
 */
export async function getCachedNews(category) {
  const hit = store.get(category)
  if (hit && Date.now() - hit.ts < TTL) {
    return { news: hit.news, fromCache: true }
  }

  // 并发去重：同一类别的请求只发一次
  if (pending.has(category)) {
    const news = await pending.get(category)
    return { news, fromCache: true }
  }

  const p = getNewsList(category)
    .then(d => d.news || [])
    .finally(() => pending.delete(category))

  pending.set(category, p)
  const news = await p
  store.set(category, { news, ts: Date.now() })
  emit()
  return { news, fromCache: false }
}

/** 预取：后台静默拉取并缓存（切页/切tab后预加载下一个类别） */
export async function prefetchNews(category) {
  try {
    await getCachedNews(category)
  } catch { /* 静默 */ }
}

/** 手动清空缓存（TTL 之外的主动刷新） */
export function clearNewsCache() {
  store.clear()
  emit()
}

/** 同步检查某类别是否已有有效缓存（不触发请求）。用于 UI 秒开判断 */
export function peekNewsCache(category) {
  const hit = store.get(category)
  const exists = !!(hit && Date.now() - hit.ts < TTL)
  return { exists }
}

/** 获取缓存状态（调试/展示用） */
export function getNewsCacheStatus() {
  return Array.from(store.entries()).map(([k, v]) => ({
    category: k, count: v.news.length, cached: Date.now() - v.ts < TTL,
  }))
}
