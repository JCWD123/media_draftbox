/**
 * 新闻 AI 摘要缓存（模块级单例）
 * - 生成过的摘要缓存起来,切换页面/类别后回来不丢失
 * - 每个摘要存 {summary, err, status} 挂到 newsSummaryCache 上
 * - 轻量方案: 模块级 Map + 简单订阅,不引入额外状态库
 */
const cache = new Map() // key=item.id -> {summary, err, status: 'done'|'loaded'}
const listeners = new Set()

function emit() {
  listeners.forEach(fn => { try { fn() } catch (e) {} })
}

/** 订阅缓存变化,返回取消函数 */
export function subscribeSummary(fn) {
  listeners.add(fn)
  return () => listeners.delete(fn)
}

/** 读某条摘要(不存在返回未加载) */
export function peekSummary(id) {
  return cache.get(id)
}

/** 写入摘要 */
export function setSummary(id, value) {
  cache.set(id, { status: 'loaded', ...value })
  emit()
}

/** 同步检查某条是否已有缓存(不触发请求)。用于 UI 秒开判断 */
export function hasSummary(id) {
  return cache.has(id)
}

/** 手动清空(调试/刷新用) */
export function clearSummaries() {
  cache.clear()
  emit()
}
