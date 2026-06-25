# Web Search Backends

Hermes 支持 7 个搜索后端。按自动检测优先级排列：

| 后端 | 认证方式 | 是否需要自托管 | 支持提取 | 环境变量 |
|------|---------|---------------|---------|---------|
| **Firecrawl** | API key | 否 | 是 | FIRECRAWL_API_KEY |
| **Parallel** | API key | 否 | 是 | PARALLEL_API_KEY |
| **Tavily** | API key | 否 | 是 | TAVILY_API_KEY |
| **Exa** | API key | 否 | 是 | EXA_API_KEY |
| **SearXNG** | URL | 是（自建实例） | 否（仅搜索） | SEARXNG_URL |
| **Brave Free** | API key | 否 | 否（仅搜索） | BRAVE_SEARCH_API_KEY |
| **DuckDuckGo** | 无 | 否 | 否（仅搜索） | ddgs Python 包 |

## Tavily（推荐，无需自托管）

最简洁的云端搜索后端。注册获取 API key（有免费额度）：

1. 去 https://tavily.com 注册
2. 设置环境变量：`echo 'TAVILY_API_KEY=tvly-...' >> ~/.hermes/.env`
3. 可选强制使用：`hermes config set web.backend tavily`
4. `/reset` 后生效

## SearXNG（自托管，免费）

隐私优先的元搜索引擎，需要自建实例：

### 部署

```bash
docker run -d --name searxng -p 8080:8080 \
  -e SEARXNG_BASE_URL=http://localhost:8080/ \
  searxng/searxng
```

或使用公共实例：https://searx.space/

### 配置

```bash
echo 'SEARXNG_URL=http://localhost:8080' >> ~/.hermes/.env
hermes config set web.backend searxng
```

### 限制

SearXNG 仅支持搜索（supports_search=True），不支持页面内容提取（supports_extract=False）。

## 配置方式

```bash
# 全局后端
hermes config set web.backend tavily

# 分能力后端（搜索用 Tavily，提取用 Firecrawl）
hermes config set web.search_backend tavily
hermes config set web.extract_backend firecrawl
```

## 自动检测

当 `web.backend` 为空时，Hermes 自动按优先级选择可用的后端：
Firecrawl → Parallel → Tavily → Exa → SearXNG → Brave Free → DuckDuckGo → 默认 Firecrawl

## 常见问题

### 后端配置了但不生效

工具配置在会话启动时加载。添加环境变量或修改 backend 后需要 `/reset` 重启会话。

### 想切换后端

修改对应的环境变量配置，然后 `/reset`。如果只想临时使用不同后端，可以在 config.yaml 的 `web.backend` 中指定。

### 使用公共 SearXNG 实例

```bash
echo 'SEARXNG_URL=https://search.sapti.me' >> ~/.hermes/.env
hermes config set web.search_backend searxng
```

注意公共实例可能不稳定或有访问限制。
