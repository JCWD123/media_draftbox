/**
 * 统一请求封装（fetch 版）
 * - 统一 baseURL('/api')
 * - 统一解包 { data, ... }
 * - 统一错误处理（网络/超时/HTTP状态)
 * - AbortController 支持
 */
const BASE_URL = '/api'
const DEFAULT_TIMEOUT = 120000 // 默认 120s（AI 生成可能较久）

class Request {
  constructor({ baseURL = BASE_URL, timeout = DEFAULT_TIMEOUT } = {}) {
    this.baseURL = baseURL
    this.timeout = timeout
    this._abortControllers = new Set()
  }

  /**
   * 发起请求
   * @param {string} path   路径（相对 /api）
   * @param {object} options { method, params, data, headers, timeout, signal }
   * @returns {Promise<any>} 已解包的响应体
   */
  async request(path, {
    method = 'GET',
    params,
    data,
    headers = {},
    timeout,
    signal,
  } = {}) {
    const url = this._buildUrl(path, params)
    const controller = new AbortController()
    this._abortControllers.add(controller)

    const timer = setTimeout(() => controller.abort(), timeout || this.timeout)
    const linkSignal = signal || controller.signal

    try {
      const resp = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json', ...headers },
        body: data !== undefined ? JSON.stringify(data) : undefined,
        signal: linkSignal,
      })

      // 尝试解析 JSON（可能为空响应体）
      const text = await resp.text()
      let body = {}
      if (text) {
        try { body = JSON.parse(text) } catch { body = { raw: text } }
      }

      if (!resp.ok) {
        throw new RequestError(resp.status, body)
      }
      return body
    } catch (err) {
      if (err.name === 'AbortError') {
        throw new RequestError(0, {}, '请求超时或已取消')
      }
      if (err instanceof RequestError) throw err
      throw new RequestError(-1, {}, `网络错误: ${err.message}`)
    } finally {
      clearTimeout(timer)
      this._abortControllers.delete(controller)
    }
  }

  get(path, options) { return this.request(path, { ...options, method: 'GET' }) }
  post(path, options) { return this.request(path, { ...options, method: 'POST' }) }
  put(path, options) { return this.request(path, { ...options, method: 'PUT' }) }
  del(path, options) { return this.request(path, { ...options, method: 'DELETE' }) }

  // 中断所有请求
  abortAll() {
    this._abortControllers.forEach(c => c.abort())
    this._abortControllers.clear()
  }

  _buildUrl(path, params) {
    let url = path.startsWith('http') ? path : `${this.baseURL}${path}`
    if (params) {
      const qs = new URLSearchParams()
      Object.entries(params).forEach(([k, v]) => {
        if (v !== undefined && v !== null) qs.append(k, v)
      })
      const q = qs.toString()
      if (q) url += `${url.includes('?') ? '&' : '?'}${q}`
    }
    return url
  }
}

// 请求错误（携带状态码 + 响应体）
class RequestError extends Error {
  constructor(status, body, message) {
    super(message || (body && body.detail) || `请求失败 (${status})`)
    this.status = status
    this.body = body
  }
}

export const request = new Request()

// 便捷：从响应中提取业务字段
export const unwrap = (res, key = 'data') => (res && res[key] !== undefined ? res[key] : res)

export default Request
