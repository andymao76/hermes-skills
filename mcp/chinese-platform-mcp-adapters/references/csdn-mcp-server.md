# CSDN MCP 服务器参考

> 源路径: `~/.hermes/mcp-servers/csdn/server.py`

## 工具

### `search_csdn(keyword, page=1, page_size=10)`

CSDN 博客搜索，使用 `https://so.csdn.net/api/v3/search` API。

- `page_size` 最大20
- 返回结果包含标题、作者、热度、摘要、链接

### `read_csdn_article(url)`

读取 CSDN 博客文章全文。内部处理：

1. 用 `requests` 获取 HTML
2. 正则提取 `#article_content` 或 `#content_views` 中的正文
3. 代码块：`<pre>` → triple backticks；`<code>` → single backtick
4. 其他 HTML tag 全部 strip
5. 正文截断 8000 字符

## 文章内容提取逻辑

```python
# 主要 selector
content_match = re.search(r'<div[^>]*id="article_content"[^>]*>(.*?)</div>\s*</div>\s*</main>', html, re.DOTALL)
# 备选
content_match = re.search(r'<div[^>]*id="content_views"[^>]*>(.*?)</div>', html, re.DOTALL)
# 作者
author_match = re.search(r'<a[^>]*class="follow-nickName"[^>]*>(.*?)</a>', html, re.DOTALL)
# 时间
time_match = re.search(r'<span[^>]*class="time"[^>]*>(.*?)</span>', html, re.DOTALL)
```

注意：CSDN 的 HTML 结构可能会更新，如果提取失败需要调整正则匹配。
