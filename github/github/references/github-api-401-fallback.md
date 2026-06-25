# GitHub API 401 降级方案：web_extract 替代

当 `mcp_github_gov1_*` 工具返回 401 Bad credentials 时，GitHub API 凭证已失效或未配置。此时可用 `web_extract` 直接从 GitHub 页面抓取仓库数据作为降级方案。

## 触发条件

```
GET https://api.github.com/search/repositories?q=xxx: 401 Bad credentials []
```

或任意 `mcp_github_gov1_*` 调用返回 401。

## 降级方案

### 获取单个仓库信息

```python
from hermes_tools import web_extract

result = web_extract(urls=["https://github.com/NousResearch/hermes-agent"])
# 从 result 中提取 stars, forks, description, latest version 等
```

页面内容经 LLM 总结后包含关键信息，例如：

```
**Stars:** 192k | **Forks:** 33.4k | **Watchers:** 755 | **Contributors:** 1,416
**License:** MIT
**Latest release:** `v0.16.0 (2026.6.5)`
```

### 批量获取多个仓库

```python
from hermes_tools import web_extract

urls = [
    "https://github.com/NousResearch/hermes-agent",
    "https://github.com/farion1231/cc-switch",
    "https://github.com/colbymchenry/codegraph",
]
results = web_extract(urls=urls)
# 每个结果含 title + content (LLM 总结的页面信息)
```

### 数据精确度说明

- web_extract 返回的是 LLM 总结后的近似值，非精确 API 值
- Stars 以 `~192,000` 或 `99.4k` 格式呈现，不是精确整数
- 无法获取：精确日增长率、仓库创建时间、commit 计数等 API 级指标
- 无法进行排序搜索（如 `sort=stars`）
- 使用 web_extract 时应在报告中标注"近似值"或"通过页面抓取获取"

### 搜索替代方案

当需要搜索仓库时（如 `mcp_github_gov1_search_repositories` 失败），可组合使用：

1. **web_search_plus** 搜索已知关键词获取初步结果
2. **web_extract** 逐个抓取仓库页面获取详细 Stars 等信息
3. 用 `execute_code` 进行数据聚合对比

```python
from hermes_tools import web_search_plus, web_extract

# 搜索
search = web_search_plus(query="github NousResearch hermes-agent stars")
# 提取仓库 URL，然后 web_extract 逐个抓取
```

## 排查 401 的根本原因

| 症状 | 根因 | 修复 |
|------|------|------|
| `mcp_github_gov1_*` 全 401 | GitHub token 过期或未配置 | 更新 `~/.hermes/config.yaml` 中 MCP GitHub 的 `GITHUB_PERSONAL_ACCESS_TOKEN` |
| 仅 `search_repositories` 401 | fine-grained token 无搜索权限 | 使用 classic token (`ghp_*`) 替代 fine-grained |
| `gh auth status` 成功但 MCP 401 | MCP 配置中的 token 与 gh CLI 不同 | 检查 `~/.hermes/config.yaml` 中 mcp_servers.github.env |
| 持续 401 无修复 | 自动降级方案已就绪 | 使用 web_extract 替代 |

## web_extract 从 GitHub 页面可提取的字段

经实践验证（2026-06-13, 2026-06-16 两次完整采集），web_extract 从 GitHub 仓库页面可可靠提取以下字段：

| 字段 | 格式示例 | 可靠性 | 备注 |
|------|---------|--------|------|
| Stars | `194k` / `102k` / `49.7k` | ✅ 精确至 k 级 | 页面标题直接显示 |
| Forks | `34.1k` / `1.4k` | ✅ | 与 Stars 同行显示 |
| Primary Language | `Python (82.4%)` | ✅ | 含百分比 |
| License | `MIT` / `Apache-2.0` | ✅ | 页面顶部 |
| Description | 完整 tagline | ✅ | 仓库标题下方 |
| Latest Release | `v0.16.0 (2026.6.5)` | ✅ | 含日期 |
| Contributors | `1,444 contributors` | ✅ | commit 统计区内 |
| Commits | `11,788 commits` | ✅ | 同上 |
| Watchers | `766` | ✅ | 页面顶部 |
| Topics | `ai, ai-agents, llm, ...` | ✅ | 标签区 |
| Repo Homepage | URL | ✅ | 项目网站链接 |
| Full README | 有截断 | ⚠️ 超过 ~5000 chars 会被 LLM 总结 |
| 3日精确增量 | 无法获得 | ❌ | 需历史快照对比 |
| 精确 Star 整数 | 无法获得 | ❌ | 只显示 194k 而非 194,283 |

## 完整工作流示例

见知识库 `~/knowledge/research/github-hermes-agent-ecosystem.md` 中 2026-06-13 和 2026-06-16 采集记录。
