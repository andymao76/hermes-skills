# 内容平台 MCP Server 构建模式

对于中文内容平台（CSDN、知乎、掘金等），构建 MCP server 时有两种常见模式。

## 模式 A：API + 网页解析（推荐）

适用于平台有可用的搜索 API，且文章内容可通过 HTTP 直接抓取。

**优点**：轻量、无浏览器依赖、冷启动快
**缺点**：可能被反爬、HTML 解析脆弱

### 典型架构 (CSDN 示例)

```python
from mcp.server.fastmcp import FastMCP
import requests, re

mcp = FastMCP("csdn")
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0...",
    "Referer": "https://so.csdn.net/",
})

@mcp.tool()
def search_csdn(keyword: str, page: int = 1) -> list:
    """搜索 CSDN 博客"""
    resp = session.get(
        "https://so.csdn.net/api/v3/search",
        params={"q": keyword, "t": "blog", "p": page}
    )
    data = resp.json()
    # 格式化返回结果...

@mcp.tool()
def read_csdn_article(url: str) -> str:
    """读取 CSDN 文章"""
    html = session.get(url).text
    # 提取标题: <h1 class="title-article">
    # 提取正文: <div id="article_content">
    # 提取作者: <a class="follow-nickName">
    # 清理HTML标签后返回
```

### 关键要点
1. **搜索接口**：先找平台是否有 JSON API（通常 `search?q=...` 带 `api` 路径）
2. **内容提取**：用正则或 BeautifulSoup 提取文章正文 DOM
3. **反爬策略**：设置合理的 User-Agent、Referer，必要时加 Cookie
4. **内容截断**：返回文本上限 8000 字符，超长截断

## 模式 B：浏览器自动化（Selenium）

适用于需要登录、动态渲染、或反爬严格的内容平台。

**优点**：能处理任何平台（跟浏览器一致）
**缺点**：需要桌面环境、启动慢、资源占用高、需 cookies 持久化

详见 [Selenium MCP Server Setup Guide](selenium-mcp-server-setup.md)

## 如何选择

| 特征 | 模式 A（API+抓取） | 模式 B（Selenium） |
|------|-------------------|-------------------|
| 平台有 JSON API | ✅ | ✅ 也可以 |
| 内容静态渲染 | ✅ 简单 | ✅ 大材小用 |
| 需要登录 | 需手动 Cookie | ✅ 浏览器登录 |
| 动态渲染/反爬严格 | ❌ 可能失败 | ✅ 可靠 |
| 服务器无桌面 | ✅ | ❌ 需 Xvfb |
| 启动速度 | 毫秒级 | 秒级 |

## 部署步骤

1. 创建 MCP server 目录：`~/.hermes/mcp-servers/<platform>/`
2. 编写 `server.py`（FastMCP + 工具函数）
3. 测试本地运行
4. 添加到 `~/.hermes/config.yaml`
5. `hermes mcp test <platform>` 验证
6. `/reload-mcp` 或重启 Hermes
