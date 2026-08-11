/**
 * 预览 HTML 隔离工具
 *
 * 后端/AI 生成的公众号 HTML 是"完整独立页面"，带 `<style>body { max-width:720px; margin:0 auto }`
 * 等元素级样式。若直接用 dangerouslySetInnerHTML 注入到 .preview 容器内，
 * CSS 选择器 `body {}` 会匹配文档全局 body，导致整个应用被限宽/污染。
 *
 * 本工具把注入的 html 做隔离处理：
 * 1. 将 `<style>` 里的 `body` 选择器改写为 `.preview`（作用域限定在预览容器，不污染全局）——始终执行
 * 2. widen=false（默认）：保留 html 自身宽度（如 720px 手机排版），适合排版转换预览（最终复制到公众号）
 * 3. widen=true：放宽 max-width 为 100%，适合草稿/AI 结果预览（宽屏方便查看全文）
 */
export function sanitizePreviewHtml(html, options = {}) {
  if (!html) return ''
  const widen = !!options.widen
  let out = html

  // 1) 把 <style> 里的 body 选择器改为 .preview（始终执行，隔离以不污染全局 body）
  out = out.replace(/<style[^>]*>([\s\S]*?)<\/style>/g, (whole, css) => {
    let fixed = css
      .replace(/body\s*(?=[{,.])/g, '.preview')
      .replace(/\bbody\b(?=\s*\{)/g, '.preview')
    return whole.replace(css, fixed)
  })

  // 2) 仅在 widen=true 时放宽宽度（宽屏查看全文）；否则保持原宽（手机排版效果）
  if (widen) {
    out = out.replace(/(\.preview\s*\{[^}]*?)max-width\s*:\s*\d+px/g, '$1max-width: 100%')
  }

  return out
}
