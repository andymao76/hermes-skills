# GitHub 生态项目监控（Ecosystem Monitoring）

通过 `gh` CLI 定时搜索 GitHub 生态项目、对比知识库、生成报告的工作流。

## 搜索引擎选择

| 方式 | 参考 | 限制 |
|------|------|------|
| **`gh search repos`** ✅ 首选 | 精确 stars、语言、fork 数 | 需 `gh` 已认证 |
| **`mcp_github_search_repositories`** | 方便但 JSON 格式受限 | MCP 认证可能失效（"Bad credentials"） |
| **`web_search`** | 无认证依赖，结果丰富 | 页码零散，需手动汇总 |

## `gh` CLI JSON 字段名陷阱

`gh search repos` 和 `gh repo view` 的 JSON 字段名不同：

**正确的字段名（`gh search repos --json`）：**
- `stargazersCount` ← 注意复数 `s` ✅
- `language` ← 小写 ✅
- `forksCount` ← 注意复数 `s` ✅
- `owner` ← 返回 `{login, id, type, ...}` 对象
- `name`, `description`, `updatedAt`, `url`

**错误的字段名（会被拒绝）：**
- `primaryLanguage` ❌ → 报错 "Unknown JSON field"
- ~~`stargazerCount` 对 search repos 是错的~~（仅 `gh repo view` 接受单数形式）

`gh repo view` 接受的字段名不同：
- `stargazerCount` ← 单数 ✅（注意：与 search repos 不同！）
- `forkCount` ← 单数 ✅

**经验法则：**
```bash
# 搜索多个仓库 → gh search repos ... --json stargazersCount,language,forksCount
# 查看单个仓库 → gh repo view ... --json stargazerCount,forkCount,description
```

## 多关键词搜索策略

单一关键词可能漏掉相关项目。推荐的组合策略：

```bash
gh search repos "hermes-agent" --sort stars --limit 30 --json name,owner,stargazersCount,description,updatedAt,url,language,forksCount

gh search repos "hermes agent" --sort stars --limit 30 --json name,owner,stargazersCount,description,updatedAt,url,language,forksCount
```

然后去重合并。注意前者结果包含 `cc-switch`、`claude-mem`、`codegraph` 等跨 Agent 工具（名称含 "hermes-agent" 引用），后者包含更多 "Hermes Agent" 直接提及的项目。

## 按 Stars 阈值精确排序

`gh search repos "stars:>N" --sort stars` 按降序返回，比 MCP 的 `search_repositories` 更可靠：

```bash
# 查找 star>500 的 hermes-agent 相关项目
gh search repos "hermes-agent stars:>500" --sort stars --limit 20 --json name,owner,stargazersCount,forksCount,description,language

# 查找所有 >1000 stars 的项目（不限关键词）
gh search repos "stars:>1000" --sort stars --limit 50 --json name,owner,stargazersCount,forksCount,description,url,language \
  | python3 -c "import json,sys; data=json.load(sys.stdin); [print(f'{r[\"stargazersCount\"]:>8,}  {r[\"owner\"][\"login\"]}/{r[\"name\"]}') for r in data]"
```

## 完整监控工作流

### 1. 搜索阶段

```bash
# 两个关键词并行搜索
K1="hermes-agent"
K2="hermes agent"

gh search repos "$K1" --sort stars --limit 30 --json name,owner,stargazersCount,description,updatedAt,url,language,forksCount > /tmp/gh_k1.json
gh search repos "$K2" --sort stars --limit 30 --json name,owner,stargazersCount,description,updatedAt,url,language,forksCount > /tmp/gh_k2.json
```

### 2. 核对单个项目细节

```bash
gh repo view owner/repo --json stargazerCount,forkCount,description,url,nameWithOwner
```

### 3. 对比知识库

- `read_file` 读取 `~/knowledge/research/github-hermes-agent-ecosystem.md`
- 按行对比每个项目的 `| name | stars |` 行
- 计算 ΔStars = 新值 − 旧值
- 识别 KB 中没有的新项目

### 4. 更新知识库

- 更新 `updated:` frontmatter 时间戳（ISO 格式如 `2026-06-10T10:00`）
- 更新每个表格行中的 Stars 和 Δ昨日
- 新增「值得关注的新项目」章节，stars>500 的一律入库
- 更新趋势汇总表的增长排名

### 5. 刷新语义索引

知识库 `.md` 更新后，必须刷新酶索引：

```bash
cd ~/knowledge && enzyme refresh
```

## 新增项目入库判断标准

| Stars 范围 | 操作 |
|-----------|------|
| > 500 | 立即入库，建新行（含描述、语言、链接） |
| 300–500 | 如果技术独特或与现有项目互补，入库 |
| < 300 | 暂列入"值得关注"表格，不展开描述 |

## 报告模板风格

保持表格形式优先（项目 | ⭐ Stars | Δ昨日 | 语言 | 说明），以 stars 逆序排列。最后用"三大看点"做文字总结。

示例摘要结构：
1. 核心数据速览（头部表格）
2. 三大看点/关键变化（文字 + 数字）
3. 新增入库项目（表格）
4. 知识库状态

## 已知坑点

- `gh` 的 `search repos` 翻页限制：`--limit` 最大 100，超出需 `--page N`
- GitHub MCP auth 可能间歇失效，此时强制回退到 `gh` CLI（terminal 工具）
- `web_search` 结果中 GitHub 的 description 可能不完整（被标记截断），需要 `gh repo view` 获取完整描述
- enzyme refresh 必须在 KB 文件写入 **之后** 执行，否则索引不更新
