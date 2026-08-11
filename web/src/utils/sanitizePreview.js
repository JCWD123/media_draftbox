/**
 * 预览 HTML 隔离工具
 *
 * 后端生成的公众号 HTML 是"完整独立页面"，带 `<style>body { max-width:720px; margin:0 auto }`
 * 等元素级样式。若直接用 dangerouslySetInnerHTML 注入到 .preview 容器内，
 * CSS 选择器 `body {}` 会匹配文档全局 body，导致整个应用被限宽/污染。
 *
 * 本工具把注入的 html 做隔离处理：
 * 1. 将 `<style>` 里的 `body` 选择器改写为 `.preview`（作用域限定在预览容器，不污染全局）
 * 2. 移除/放宽 body 的 max-width（预设 720px 变成 100%），让桌面预览利用宽屏、便于查看
 */
export function sanitizePreviewHtml(html) {
  if (!html) return ''
  let out = html

  // 1) 把 <style> 里的 body 选择器改为 .preview（含 body 前后可能有注释/html 选择器并存的情况）
  //    匹配 <style> 内容，把独立的 body{ ... } 及 body { ... } 替换为 .preview
  out = out.replace(/<style[^>]*>([\s\S]*?)<\/style>/g, (whole, css) => {
    // 仅处理作为选择器单词的 body（后面跟 { 或 , 或 选择器边界）
    let fixed = css
      .replace(/body\s*(?=[{,.])/g, '.preview')
      // 若已是 body 后跟空格再 { ，上面已转；再兜底处理 body { 形式
      .replace(/\bbody\b(?=\s*\{)/g, '.preview')
    return whole.replace(css, fixed)
  })

  // 2) 放宽预览区的 max-width / 强制满宽（预览阅读友好）
  out = out.replace(/(\.preview\s*\{[^}]*?)max-width\s*:\s*\d+px/g, '$1max-width: 100%')

  return out
}
