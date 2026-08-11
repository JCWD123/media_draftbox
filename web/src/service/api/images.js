import { request } from '../request'

// 图片搜索
export const searchImages = (query, count = 12) =>
  request.post('/images/search', { data: { query, count }, timeout: 30000 })
