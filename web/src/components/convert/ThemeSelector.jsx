import { memo } from 'react'

// wewrite 全部主题（对应后端 /api/themes 返回的 18 个）+ 精品「学长十一」主题
export const WEWRITE_THEMES = [
  { id: 'premium', name: '★ 学长十一·精选' },
  { id: 'professional-clean', name: '专业简洁' },
  { id: 'minimal', name: '极简' },
  { id: 'github', name: 'GitHub' },
  { id: 'newspaper', name: '报纸' },
  { id: 'bold-navy', name: '深蓝粗体' },
  { id: 'bauhaus', name: '包豪斯' },
  { id: 'bold-green', name: '墨绿' },
  { id: 'bytedance', name: '科技字节' },
  { id: 'elegant-rose', name: '雅致玫瑰' },
  { id: 'focus-red', name: '焦点红' },
  { id: 'impeccable', name: '无可挑剔' },
  { id: 'ink', name: '墨韵' },
  { id: 'lobster-notes', name: '龙虾笔记' },
  { id: 'midnight', name: '午夜' },
  { id: 'minimal-gold', name: '极简金' },
  { id: 'sspai', name: '少数派' },
  { id: 'tech-modern', name: '科技现代' },
  { id: 'warm-editorial', name: '温暖编辑' },
]

/**
 * wewrite 主题选择器
 */
const ThemeSelector = memo(({ value, onChange }) => (
  <select value={value} onChange={e => onChange(e.target.value)} className="theme-select">
    {WEWRITE_THEMES.map(t => (
      <option key={t.id} value={t.id}>{t.name}</option>
    ))}
  </select>
))

export default ThemeSelector
