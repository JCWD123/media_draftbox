# DraftBox GitHub Flow 规范

本仓库采用 **GitHub Flow** 轻量分支模型（参考一线大厂 Git 规范），适合持续交付、快速迭代的单人/小团队项目。

## 一、分支模型（GitHub Flow）

只有一条长期分支 **`main`**（生产/稳定，始终保持可部署）。所有开发都在短期的 **feature 分支**上进行。

```
main ────────────────●──────────────●──→  （始终可部署）
    \              /            /
     feature/a──●──            feature/b──●──
         开发+提交            PR审查后合并
```

核心流程：
1. 从 `main` 创建 feature 分支
2. 在 feature 分支上开发并提交（Conventional Commits）
3. 创建 Pull Request
4. 代码审查通过后**合并到 main**（本地直接合并，远程建议开 PR）
5. 合并后推送/部署

## 二、分支命名规范

格式：`<类型>/<内容>`，内容用连字符，一眼看出用途。

| 前缀 | 用途 | 示例 |
|------|------|------|
| `feature/` | 新功能开发 | `feature/custom-news-search` |
| `fix/` | 修复 bug | `fix/search-result-lang` |
| `refactor/` | 代码重构 | `refactor/convert-engine` |
| `docs/` | 文档更新 | `docs/github-flow-guide` |
| `chore/` | 构建/工具 | `chore/update-deps` |

示例：
```
feature/ai-news-summary
feature/jina-paid-search
fix/news-cache-persist
docs/github-flow-guide
```

## 三、Commit Message 规范（Conventional Commits）

格式：`<type>(<scope>): <subject>`

**type 必填**：

| type | 含义 | 示例 |
|------|------|------|
| `feat` | 新增功能 | `feat(user): 添加登录` |
| `fix` | 修复 bug | `fix(api): 修复超时` |
| `docs` | 文档 | `docs(readme): 更新说明` |
| `refactor` | 重构 | `refactor(order): 拆分Service` |
| `test` | 测试 | `test(auth): 增加单测` |
| `chore` | 工具/构建 | `chore: 升级依赖` |

**subject 要求**：
- 一般现在时、祈使句（`add` 不是 `added`）
- 首字母小写，句尾不加句号
- 不超过 50 字符

完整示例：
```
feat(news): 新闻素材新增AI摘要功能
fix(search): 修复搜索结果英文为主问题
docs(git): 新增GitHub Flow规范
```

## 四、PR 流程（合并到 main 前）

1. 完成 feature 分支开发，测试通过（本项目：`pytest` 全部通过）
2. 创建 PR：合并 `feature/xxx` → `main`
3. 填写 PR 模板（见 `.github/PULL_REQUEST_TEMPLATE.md`）
4. 代码审查通过后合并
5. 合并后立即推送部署

## 五、本地常用流程

```bash
# 1. 确保 main 最新
git checkout main && git pull origin main

# 2. 建 feature 分支
git checkout -b feature/custom-news-search

# 3. 开发、提交（Conventional Commits）
git add -A
git commit -m "feat(news): 新增自定义搜索"

# 4. 合并回 main（单人项目本地合并）
git checkout main
git merge --no-ff feature/custom-news-search

# 5. 推送
git push origin main
```

## 六、安全红线

- **密钥/凭证绝不进仓库**：API key 只存 `~/.draftbox/config.yaml`（仓库外）
- 提交前检查 `git status`，确认无 `_verify`/`_debug` 临时脚本残留
- 敏感环境变量用 CI 密文，不进历史
