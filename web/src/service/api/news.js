import { request } from '../request'

// 新闻分类
export const getCategories = () => request.get('/news/categories')

// 新闻列表
export const getNewsList = (category, page = 1, pageSize = 20) =>
  request.post('/news/list', { data: { category, page, page_size: pageSize } })

// 自定义新闻搜索（ddgs 实时搜索，结果可勾选为写作素材）
export const searchNews = (query, limit = 12) =>
  request.post('/news/search', { data: { query, limit }, timeout: 30000 })
