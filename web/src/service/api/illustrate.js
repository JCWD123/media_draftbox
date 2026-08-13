import { request } from '../request'

// 根据发布物料.md 给 HTML 配图
export const illustrateArticle = (html, materialMd) =>
  request.post('/illustrate', { data: { html, material_md: materialMd }, timeout: 300000 })
