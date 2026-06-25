# CSDN MCP Server 构建参考

CSDN API-based MCP server 的完整实现，作为 API+网页抓取模式（模式 A）的参考模板。

## 搜索接口

CSDN 搜索有 JSON API，无需登录：

```
GET https://so.csdn.net/api/v3/search
参数: q=keyword, t=blog, p=page, s=0, tm=0, lv=-1, ft=0, l=""
返回: {"result_vos": [...], "total": N}
```

结果字段：
- `result_vos[].title` — 标题（含 HTML 标签，需清理）
- `result_vos[].url` — 文章链接
- `result_vos[].author` — 作者
- `result_vos[].body` — 摘要
- `result_vos[].digg` — 热度/点赞数

## 内容提取

文章页面解析关键 DOM 元素：

| 内容 | 选择策略 |
|------|---------|
| 标题 | `<h1 class="title-article">` 或 `<title>` |
| 正文 | `<div id="article_content">` 或 `<div id="content_views">` 或 `<article>` |
| 作者 | `<a class="follow-nickName">` |
| 时间 | `<span class="time">` |

HTML 清理：保留 `<pre><code>` 块标记，其余标签用正则去除，避免丢失代码块格式。

## 通用提取函数

```python
import re

def clean_html(text: str) -> str:
    text = re.sub(r'<pre[^>]*>', '\n```\n', text)
    text = re.sub(r'</pre>', '\n```\n', text)
    text = re.sub(r'<code[^>]*>', '`', text)
    text = re.sub(r'</code>', '`', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text
```

## 工具签名模板

```python
@mcp.tool()
def search_platform(keyword: str, page: int = 1, page_size: int = 10) -> list[TextContent]:
    """搜索平台文章
    Args:
        keyword: 搜索关键词
        page: 页码，从1开始
        page_size: 每页条数，最多20
    """

@mcp.tool()
def read_platform_article(url: str) -> list[TextContent]:
    """读取平台文章内容
    Args:
        url: 文章完整URL
    """
```

## Config.yaml 配置

```yaml
mcp_servers:
  <platform>:
    command: /home/andymao/.hermes/hermes-agent/venv/bin/python3
    args: ["/home/andymao/.hermes/mcp-servers/<platform>/server.py"]
    connect_timeout: 15
    timeout: 30
```

## 项目结构

```
~/.hermes/mcp-servers/<platform>/
└── server.py    # 单文件，零依赖（requests + mcp）
```
