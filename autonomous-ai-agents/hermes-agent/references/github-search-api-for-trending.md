# GitHub Search API: 替代 Trending 页面抓取

## 为什么需要 API 方案

`github.com/trending` 页面在某些网络环境下（无代理、GFW 干扰）经常超时或返回不完整内容。
GitHub Search API (`api.github.com`) 通常更稳定，且不限制爬虫。

## 方案对比

| 维度 | Trending 页面抓取 | Search API |
|------|------------------|------------|
| 数据源 | github.com/trending | api.github.com |
| 稳定性 | 较差（HTML 爬取易超时） | 较好（REST API） |
| 数据特征 | 今日热门（star 增长量） | 按创建时间 + star 数排序 |
| 依赖 | 正则解析 HTML（脆弱） | JSON 解析（稳定） |
| 频率限制 | 无官方限制 | 未认证 60 req/h, 认证 5000 req/h |
| 网络要求 | 需直连 github.com | 需直连 api.github.com |

## API 方案核心逻辑

```python
import urllib.request, urllib.parse, json
from datetime import datetime, timedelta, timezone

CST = timezone(timedelta(hours=8))
two_days_ago = (datetime.now(CST) - timedelta(days=2)).strftime("%Y-%m-%d")

query = f"created:>={two_days_ago} stars:>50"
url = f"https://api.github.com/search/repositories?q={urllib.parse.quote(query)}&sort=stars&order=desc&per_page=10"

req = urllib.request.Request(url, headers={
    "User-Agent": "HermesBot/1.0",
    "Accept": "application/vnd.github+json",
})

with urllib.request.urlopen(req, timeout=15) as resp:
    data = json.loads(resp.read().decode("utf-8"))

for item in data.get("items", [])[:5]:
    name = item["full_name"]
    desc = item.get("description") or "暂无描述"
    lang = item.get("language") or "N/A"
    stars = item["stargazers_count"]
    forks = item["forks_count"]
    url = item["html_url"]
    topics = item.get("topics", [])
    print(f"【{i}】{name}")
    print(f"📝 {desc}")
    print(f"🔤 {lang}  ⭐ {stars}  🍴 {forks}")
    print(f"🔗 {url}")
```

## 搜索条件调参

- `created:>={date}` — 按创建时间过滤。推荐 2-3 天，太短可能数据不足。
- `stars:>50` — 过滤低质量项目。可调高至 200+ 减少噪声。
- `sort=stars&order=desc` — 按 star 数降序，等效于"最热门新项目"。
- `per_page=10` — 取前 N 个再截断，确保足够候选。

### 其他常见查询模式

- **今日特定语言热门**: `q=language:python created:>={date}&sort=stars`
- **带关键词过滤**: `q=LLM OR agent OR RAG created:>={date}&sort=stars`
- **关注增长而非绝对值**: API 无今日 star 增量字段。如需近似，可每日缓存并用差值估算。

## 与 Trending 页面数据的差异

1. Trending 按 **今日 star 增长量** 排序，API 按 **总 star 数** 排序 — 结果不同但都反映社区热度。
2. Trending 会显示昨日 0 star 今日暴涨的项目；API 需要项目有 ≥1 个 star 才能被搜索到（且 `stars:>50` 过滤了更低热度的项目）。
3. API 返回的数据更结构化、更完整（有 topics, license, 更新时间等字段）。
4. API 不会出现在 Trending 页面上的"sponsors"类项目。

## 生产环境最佳实践

### 核心教训：网络受限时直接改用 API，不要死磕 Trending 页面

当 `github.com` 连接超时时（常见于无代理的服务器环境），**重试和加超时解决不了问题** — 这是网络层被限制，不是瞬时故障。直接改用 Search API：

```python
# 快速判断 — 不要等 urllib 的 15s 超时
import socket
try:
    socket.create_connection(("api.github.com", 443), timeout=5)
except OSError:
    print("api.github.com 不可达，检查网络或代理")
    exit(1)
```

### 生产级脚本模板

完整的可运行脚本见 `scripts/github-search-api-trending.py`，包含：

- **配置参数** — LIMIT, MIN_STARS, LOOKBACK_DAYS, CACHE_ENABLED 均可调
- **网络预检** — `socket.create_connection` 快速判断，失败即退出（不空耗15s）
- **3次重试** — 间隔3秒，应对 DNS 抖动/瞬时网络波动
- **缓存** — 当日首次抓取后生成缓存文件，后续调用直接输出
- **Topics 标签** — 展示最多3个项目标签，增加可读性
- **无外部依赖** — 只用 urllib 标准库，Hermes venv 和系统 Python 都能跑

### 常见故障排查

| 现象 | 原因 | 解决 |
|------|------|------|
| `urlopen error timed out` | GitHub 被墙/DNS 污染 | 改用 Search API（Trending 页面常被墙，api.github.com 通常可达） |
| `Temporary failure in name resolution` | DNS 服务器不可用 | 检查 /etc/resolv.conf，或改用 8.8.8.8 |
| `403 rate limit exceeded` | 未认证 API 调用超限（60 req/h） | 加 `Authorization: token YOUR_GITHUB_TOKEN` header，提升到 5000 req/h |
| 搜索结果太少或为空 | `MIN_STARS` 过高或 `LOOKBACK_DAYS` 太短 | 降低 MIN_STARS 或增加 LOOKBACK_DAYS |
| 脚本在 cron 中失败但手动运行成功 | PATH 或工作目录不同 | 使用 `workdir` 参数或在脚本开头用绝对路径 |

### 双脚本策略（最高可靠性）

如果环境网络有时可达、有时不可达，可建立两个 cron job 互为备份：

- **主任务**: `github-search-api-trending.py`，投递到目标平台
- **备用任务**: `github-trending-scraper.py`，投递到同一平台
- 两个脚本都带缓存，谁先成功当日就不再重复发送

### 注意 Search API 的局限

- API 查不到 `stars:0` 的项目（今天才创建、零 star 但今日增长迅猛的项目会被漏掉）
- 排序按总 star 而不是今日增量，和 Trending 页面的排序不同
- 未认证时 60 req/h 的限制很严格，建议加上 GitHub Token
