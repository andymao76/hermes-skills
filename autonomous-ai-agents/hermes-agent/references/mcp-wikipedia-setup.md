# Wikipedia MCP Server 配置

## 方式一：Python 包（推荐，支持中文 + 缓存）

### 安装

```bash
# 在 Hermes venv 中安装
~/.hermes/hermes-agent/venv/bin/pip install wikipedia-mcp
```

### 配置（config.yaml）

```yaml
mcp_servers:
  wikipedia:
    command: /home/andymao/.hermes/hermes-agent/venv/bin/wikipedia-mcp
    args: ["--language", "zh", "--enable-cache"]
    env:
      HTTPS_PROXY: "http://127.0.0.1:7897"    # GFW 环境必须
      HTTP_PROXY: "http://127.0.0.1:7897"     # GFW 环境必须
    connect_timeout: 30
    timeout: 120
```

**注意：** `env` 段中的 `HTTPS_PROXY`/`HTTP_PROXY` 是**必须的**——Python 的 `wikipedia-api` 库会读取环境变量来决定代理。即使 Hermes 主进程已有代理，子进程不自动继承。

### 可用工具（22 个）

| 核心工具 | 功能 | 参数 |
|----------|------|------|
| `search_wikipedia` | 搜索文章 | `query` (string, required) |
| `get_article` | 获取完整内容 | `title` 或 `page_id` |
| `get_summary` | 获取摘要 | `title` (string) |
| `extract_key_facts` | 提取关键事实 | `title` + 可选 `pageId` |
| `get_sections` | 获取章节列表 | `title` |
| `get_related_topics` | 相关主题 | `title` |
| `summarize_article_for_query` | 按查询获取摘要 | `title` + `query` |
| `test_wikipedia_connectivity` | 连接诊断 | 无参数 |

### 语言支持

- `--language zh`：搜索中文 Wikipedia（zh.wikipedia.org）
- `--language en`：搜索英文 Wikipedia（默认）
- `--enable-cache`：本地缓存减少重复请求

### 验证

```bash
hermes mcp test wikipedia
# 应看到 22 个 tools 可用
```

## 方式二：npx（更快但有代理问题）

```json
{
  "mcp_servers": {
    "wikipedia": {
      "command": "npx",
      "args": ["-y", "wikipedia-mcp@latest"],
      "env": {
        "HTTPS_PROXY": "http://127.0.0.1:7897",
        "HTTP_PROXY": "http://127.0.0.1:7897"
      }
    }
  }
}
```

**注意：** npx 版本在 GFW 环境下可能遇到 `UND_ERR_CONNECT_TIMEOUT`（nodejs fetch 的 10s 默认超时），env 中的 proxy 也可能不被 npx 子进程继承。Python 版更稳定。

## GFW 环境下的网络配置

Wikipedia（en.wikipedia.org 和 zh.wikipedia.org）都被 GFW 封锁，必须通过代理访问。

### 关键：子进程不自动继承代理

即使父 shell 已有 `HTTPS_PROXY`，MCP server 子进程也不会自动继承（取决于 `StdioServerParameters` 的实现）。必须**显式**在 `config.yaml` 的 `env` 段指定。

### 代理测试命令

```bash
# 测试 Wikipedia API 是否可通过代理访问
curl -s --proxy http://127.0.0.1:7897 \
  "https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch=AI&format=json" \
  -o /dev/null -w "%{http_code}"
# 返回 200 说明代理可用
```

### 限流注意

Wikipedia API 对高频率请求有限流（429 Too Many Requests）。建议：
- 启用 `--enable-cache` 减少重复请求
- 两次搜索之间间隔至少 1 秒
- 使用 `get_summary` 替代 `get_article` 获取完整内容（摘要更快）
