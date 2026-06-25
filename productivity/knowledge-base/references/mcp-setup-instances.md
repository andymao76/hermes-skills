# MCP 服务器安装与配置速查

当前环境已安装的 MCP 服务器配置详情与关键注意点。

## Wikipedia MCP（Python 版，v2.0.1）

**来源：** PyPI `wikipedia-mcp`（npm 版 `wikipedia-mcp` 也发布但不需要 npm）

### 安装

```bash
source ~/.hermes/hermes-agent/venv/bin/activate
pip install wikipedia-mcp
```

### 配置 (config.yaml)

```yaml
mcp_servers:
  wikipedia:
    command: /home/andymao/.hermes/hermes-agent/venv/bin/wikipedia-mcp
    args: ["--language", "zh", "--enable-cache"]
    env:
      HTTPS_PROXY: "http://127.0.0.1:7897"
      HTTP_PROXY: "http://127.0.0.1:7897"
    connect_timeout: 30
    timeout: 120
```

### 关键注意

- **GFW 封锁**：`en.wikipedia.org` 和 `zh.wikipedia.org` 均被封锁，必须通过代理访问
- **Python 包 vs npm 包**：Python 版 `wikipedia-mcp` 提供 22 个工具（search, get_article, get_summary, extract_key_facts 等），npm 版只有 2 个（search, readArticle）
- **`--language zh`**：优先返回中文 Wikipedia 结果
- **`--enable-cache`**：缓存已查询的文章，减少重复请求
- **`StdioServerParameters.env` 必须显式设置**：MCP 子进程不会继承父 shell 的代理环境变量

### 可用工具（22个）

核心工具：`search_wikipedia` (搜索)、`get_article` (全文)、`get_summary` (摘要)、`extract_key_facts` (关键事实)、`get_sections` (章节)、`get_related_topics` (相关主题)、`test_wikipedia_connectivity` (诊断)

### 直连验证

```python
import requests
r = requests.get("https://en.wikipedia.org/w/api.php",
    params={"action": "query", "list": "search", "srsearch": "AI Agent", "format": "json"},
    timeout=10, headers={"User-Agent": "Test/1.0"})
# 直连超时 → 需代理
r = requests.get("https://en.wikipedia.org/w/api.php", ...,
    proxies={"https": "http://127.0.0.1:7897"})
# 代理可通
```

---

## Taobao/Tmall MCP（Python + Playwright）

**来源：** GitHub [JeremyDong22/taobao_mcp](https://github.com/JeremyDong22/taobao_mcp)

### 安装

```bash
cd /home/andymao/.hermes
git clone https://github.com/JeremyDong22/taobao_mcp.git
cd taobao_mcp
source /home/andymao/.hermes/hermes-agent/venv/bin/activate
pip install -e .
```

需修改 `taobao_scraper.py` 中 `headless=False` 为 `headless=True`（服务器无显示器时）。

### 配置 (config.yaml)

```yaml
mcp_servers:
  taobao:
    command: /home/andymao/.hermes/hermes-agent/venv/bin/python3
    args: [/home/andymao/.hermes/taobao_mcp/server.py]
    env:
      DISPLAY: ":99"      # 如有 Xvfb 运行中
      no_proxy: "*"
      NO_PROXY: "*"
    connect_timeout: 60
    timeout: 120
```

### 可用工具（2个）

1. `taobao_initialize_login` — 初始化浏览器会话，需扫码登录（headless 模式下不可用）
2. `taobao_fetch_product` — 获取商品完整信息（标题、价格、图片、评价、问答）

### 关键注意

- **需第一次手动登录**（通过 Playwright headed 浏览器扫码）
- **已登录后**：会话持久化在 `user_data/chrome_profile/` 目录，重启后可复用
- **浏览器工具备选**：当 MCP 不可用时，通过 `agent-browser navigate <商品URL>` 直接访问
- **Playwright Chromium** 已安装在 `~/.cache/ms-playwright/chromium-1223/`

---

## CSDN MCP

**来源：** Hermes skills hub

通过 `hermes skills install <csdn-id>` 安装。

---

## Zhihu MCP

**来源：** Hermes skills hub

通过 `hermes skills install <zhihu-id>` 安装。

---

## MCP 通用排障

| 症状 | 原因 | 解决 |
|------|------|------|
| `hermes mcp test` 成功但工具调用失败 | 当前会话的 MCP 连接是旧的 | `/reload-mcp` 重新加载 |
| 工具调用 `Connection closed` | stdio bridge 进程僵死或端口占用 | 清理残留进程后恢复 |
| 工具调用 `timeout after 120s` | 网络慢或对方服务超时 | 先试简单关键词（无 filters） |
| 断路器触发 `unreachable after N consecutive failures` | MCP 服务器连续异常 | 等待 cooldown ~60s 或重启 Hermes |
| 代理相关错误 (ConnectTimeoutError) | 子进程未继承代理 env | 在 config.yaml 的 `env:` 中显式设置 |
