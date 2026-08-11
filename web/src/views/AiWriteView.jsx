import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import TopicInput from '../components/aiwrite/TopicInput'
import MediaOptions from '../components/aiwrite/MediaOptions'
import NewsPicker from '../components/aiwrite/NewsPicker'
import TagBar from '../components/aiwrite/TagBar'
import WarningBox from '../components/aiwrite/WarningBox'
import ResultView from '../components/aiwrite/ResultView'
import Button from '../components/common/Button'
import { getCategories, getNewsList } from '../service/api/news'
import { generateArticle, getMediaStatus } from '../service/api/aiwrite'
import { useApp } from '../utils/AppContext'

/**
 * AI 写作页（三模态编排）
 */
export default function AiWriteView() {
  const { setMarkdown, html, setHtml, saveAsDraft, showToast } = useApp()
  const navigate = useNavigate()
  const [topic, setTopic] = useState('')
  const [withImages, setWithImages] = useState(true)
  const [withVideo, setWithVideo] = useState(false)
  const [categories, setCategories] = useState([])
  const [activeCat, setActiveCat] = useState('TECH')
  const [news, setNews] = useState([])
  const [selected, setSelected] = useState(new Set())

  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState('')
  const [title, setTitle] = useState('')
  const [tags, setTags] = useState([])
  const [vertical, setVertical] = useState('')
  const [warnings, setWarnings] = useState([])
  const [videoStatus, setVideoStatus] = useState('')
  const pollTimer = useRef(null)

  useEffect(() => {
    getCategories().then(d => {
      setCategories((d.data || []).map(c => ({ id: c.category_code, name: c.category_name })))
    }).catch(() => {})
  }, [])

  useEffect(() => {
    getNewsList(activeCat).then(d => setNews(d.news || [])).catch(() => setNews([]))
  }, [activeCat])

  useEffect(() => () => {
    if (pollTimer.current) clearInterval(pollTimer.current)
  }, [])

  const toggleNews = (id) => {
    setSelected(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else {
        if (next.size >= 10) { showToast('warn', '最多选 10 条新闻'); return prev }
        next.add(id)
      }
      return next
    })
  }

  const pollVideo = (draftId) => {
    if (pollTimer.current) clearInterval(pollTimer.current)
    pollTimer.current = setInterval(async () => {
      try {
        const d = await getMediaStatus(draftId)
        if (d.status === 'done') {
          clearInterval(pollTimer.current)
          setVideoStatus('✅ 视频已生成')
          if (d.html) setHtml(d.html)
        } else if (d.status === 'failed') {
          clearInterval(pollTimer.current)
          setVideoStatus(`❌ 视频生成失败: ${d.error || ''}`)
        } else {
          setVideoStatus('⏳ 视频生成中（约 1-5 分钟）...')
        }
      } catch { clearInterval(pollTimer.current) }
    }, 5000)
  }

  const generate = async () => {
    if (!topic.trim()) { showToast('warn', '请输入话题/核心思路'); return }
    setLoading(true)
    setResult(''); setHtml(''); setTags([]); setVertical(''); setWarnings([]); setVideoStatus('')
    try {
      const d = await generateArticle({
        topic: topic.trim(), news_ids: [...selected],
        with_images: withImages, with_video: withVideo, max_images: 4, max_videos: 1
      })
      if (!d.success) { setWarnings([d.error]); return }
      setResult(d.content); setHtml(d.html); setTags(d.tags || []); setTitle(d.title || '')
      if (d.vertical_check?.drifted) setVertical(`⚠ 垂直度已校准: ${d.vertical_check.note || ''}`)
      else if (d.vertical_check?.domain) setVertical(`✓ 垂直领域: ${d.vertical_check.domain}`)
      else setVertical('')
      setWarnings(d.warnings || [])
      if (d.video_pending) pollVideo(d.draft_id)
    } catch (e) {
      setWarnings([`生成失败: ${e.message}`])
    } finally {
      setLoading(false)
    }
  }

  const saveDraft = () => {
    saveAsDraft(title || topic || 'AI生成文章', result, html || '')
  }

  const openConvert = () => {
    // 排版管理页直接显示 AI 生成的最新 html
    setMarkdown(result)
    navigate('/')
  }

  return (
    <div className="panel full ai-write">
      <h2>🤖 AI 写作（文字 + 图片 + 视频）</h2>
      <div className="toolbar">
        <TopicInput value={topic} onChange={setTopic} onEnter={generate} />
        <Button variant="primary" onClick={generate} loading={loading}>
          {loading ? '生成中' : '🚀 生成'}
        </Button>
      </div>
      <MediaOptions
        withImages={withImages} onImagesChange={setWithImages}
        withVideo={withVideo} onVideoChange={setWithVideo}
        videoStatus={videoStatus}
      />
      <NewsPicker
        categories={categories} activeCategory={activeCat}
        onCategoryChange={setActiveCat}
        news={news} selectedIds={selected}
        onToggle={toggleNews}
        onClear={() => setSelected(new Set())}
      />
      <TagBar tags={tags} vertical={vertical} />
      <WarningBox warnings={warnings} />
      <ResultView
        title={title} markdown={result} html={html}
        onOpenConvert={openConvert}
        onSaveDraft={saveDraft}
      />
    </div>
  )
}
