import { request } from '../request'

// 新闻分类
export const getCategories = () => request.get('/news/categories')

// 新闻列表
export const getNewsList = (category, page = 1, pageSize = 20) =>
  request.post('/news/list', { data: { category, page, page_size: pageSize } })
