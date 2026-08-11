import { request } from '../request'

// AI 三模态生成（文字+图片+视频）
export const generateArticle = (payload) =>
  request.post('/write/generate', { data: payload, timeout: 300000 }) // 5 分钟

// 视频状态轮询
export const getMediaStatus = (draftId) =>
  request.get('/write/media-status', { params: { draft_id: draftId }, timeout: 15000 })
