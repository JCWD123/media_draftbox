import { request } from '../request'

// 主题列表
export const getThemes = () => request.get('/themes')

// Markdown → 微信HTML
export const convertMarkdown = (markdown, theme) =>
  request.post('/convert', { data: { markdown, theme }, timeout: 60000 })
