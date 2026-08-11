import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import TopicInput from '../components/aiwrite/TopicInput'
import MediaOptions from '../components/aiwrite/MediaOptions'
import NewsPicker from '../components/aiwrite/NewsPicker'
import NewsCheckItem from '../components/aiwrite/NewsCheckItem'
import TagBar from '../components/aiwrite/TagBar'
import WarningBox from '../components/aiwrite/WarningBox'
import ResultView from '../components/aiwrite/ResultView'
import Button from '../components/common/Button'
import { getCategories, getNewsList, searchNews } from '../service/api/news'
import { generateArticle, getMediaStatus } from '../service/api/aiwrite'
import { useApp } from '../utils/AppContext'

/**
 * AI 写作页（三模态编排）
 */
export default function AiWriteView() {
  const {
    setMarkdown, html, setHtml, saveAsDraft, showToast,
    searchQuery, setSearchQuery, searchResults, setSearchResults, searching, setSearching,
    selectedNews: selected, setSelectedNews: setSelected,
  } = useApp()
  const navigate = useNavigate()
  const [topic, setTopic] = useState('')
  const [withImages, setWithImages] = useState(true)
  const [withVideo, setWithVideo] = useState(false)
  const [categories, setCategories] = useState([])
  const [activeCat, setActiveCat] = useState('TECH')
  const [news, setNews] = useState([])
  const [newsLoading, setNewsLoading] = useState(false) // 切换类别时加载态
  const newsReqSeq = useRef(0) // 新闻请求序号，防竞态（快速切换类别时只认最新一次）

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
    // 切换类别：立即清空旧类别新闻 + 显示加载态，避免残留上个类别的新闻
    setNews([])
    setNewsLoading(true)
    const seq = ++newsReqSeq.current // 本类别请求序号
    getNewsList(activeCat)
      .then(d => {
        // 竞态防护：若期间已经切到别的类别（seq 变了），丢弃本次过期响应
        if (seq === newsReqSeq.current) setNews(d.news || [])
      })
      .catch(() => {
        if (seq === newsReqSeq.current) setNews([])
      })
      .finally(() => {
        if (seq === newsReqSeq.current) setNewsLoading(false)
      })
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

  // 自定义新闻搜索（ddgs 实时搜索，结果进入可勾选列表）
  const doSearch = async () => {
    if (!searchQuery.trim()) { showToast('warn', '请输入搜索关键词'); return }
    setSearching(true)
    try {
      const res = await searchNews(searchQuery.trim(), 12)
      if (!res.news || res.news.length === 0) {
        showToast('info', res.error || '未搜索到相关新闻')
        setSearchResults([])
      } else {
        setSearchResults(res.news)
        showToast('success', `搜到 ${res.news.length} 条新闻`)
      }
    } catch (e) {
      showToast('error', `搜索失败: ${e.message}`)
      setSearchResults([])
    } finally {
      setSearching(false)
    }
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
        loading={newsLoading}
      />

      {/* 自定义新闻搜索（ddgs 实时搜索） */}
      <div className="news-select custom-search">
        <div className="news-select-header">
          <h3>🔍 自定义搜索新闻（实时）</h3>
          <div className="search-bar">
            <input
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && doSearch()}
              placeholder="输入关键词，如: 开源AI模型 / 视频生成 / agent框架..."
              className="search-input"
            />
            <Button variant="primary" onClick={doSearch} loading={searching}>
              {searching ? '搜索中' : '🔍 搜索'}
            </Button>
          </div>
        </div>
        {searchResults.length > 0 && (
          <>
            <div className="search-result-count">
              搜索到 {searchResults.length} 条，勾选后可作为写作素材
              <button className="link-btn" onClick={() => setSelected(new Set())}>清空选中</button>
            </div>
            <div className="news-select-list">
              {searchResults.map(item => (
                <NewsCheckItem
                  key={item.id}
                  item={item}
                  checked={selected.has(item.id)}
                  onToggle={() => toggleNews(item.id)}
                />
              ))}
            </div>
          </>
        )}
        {searchResults.length === 0 && !searching && (
          <div className="news-empty">输入关键词搜索 AI 圈/技术类实时新闻，如「开源AI模型」「Agent框架」</div>
        )}
      </div>

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
