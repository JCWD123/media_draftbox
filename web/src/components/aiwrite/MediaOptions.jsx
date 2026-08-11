import { memo } from 'react'

/**
 * 媒体生成选项（配图/视频勾选 + 视频状态）
 */
const MediaOptions = memo(({ withImages, onImagesChange, withVideo, onVideoChange, videoStatus }) => (
  <div className="toolbar">
    <label className="media-opt">
      <input type="checkbox" checked={withImages} onChange={e => onImagesChange(e.target.checked)} />
      生成配图（默认）
    </label>
    <label className="media-opt">
      <input type="checkbox" checked={withVideo} onChange={e => onVideoChange(e.target.checked)} />
      生成视频（约1-5分钟）
    </label>
    {videoStatus && <span className="video-status">{videoStatus}</span>}
  </div>
))

export default MediaOptions
