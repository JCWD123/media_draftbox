import { request } from '../request'

// 草稿列表
export const listDrafts = () => request.get('/drafts')

// 获取单个草稿（返回 title/markdown/html）
export const getDraft = (filename) => request.get(`/drafts/${filename}`)

// 保存草稿（title + markdown 源 + wewrite HTML）
export const saveDraft = (title, content, html = '') =>
  request.post('/drafts', { data: { title, content, html }, timeout: 30000 })

// 删除草稿
export const deleteDraft = (filename) => request.del(`/drafts/${filename}`)
