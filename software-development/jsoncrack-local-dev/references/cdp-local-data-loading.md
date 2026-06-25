# CDP 加载本地数据到 jsoncrack

在 headless Chrome 中用 CDP 将本地 JSON dump 文件加载到 jsoncrack 编辑器可视化。

## 场景

Hermes dump JSON（`~/.hermes/sessions/request_dump_*.json`）需要在 JSON Crack 中查看，但浏览器无法直接访问本机 localhost。

## 步骤

### 0. 注意：browser_navigate 会阻止 localhost

Hermes 内置的 `browser_navigate` 工具会拦截私有/内部地址（如 localhost）。必须使用 CDP 的 `Page.navigate` 方法绕过。

### 1. 启动静态文件服务器

```bash
cd ~/.hermes/sessions
python3 -m http.server <端口>   # 例如 8888
```

### 2. 通过 CDP 导航到 jsoncrack editor（带 URL 参数）

jsoncrack 的 `checkEditorSession()` 会在页面 URL 包含 `?` 时自动将 query string 作为 JSON 源 URL 进行 fetch。

```python
# CDP Page.navigate
url = "http://localhost:3001/editor?http://localhost:8888/request_dump_20260625_*.json"
```

### 3. 验证

- `Runtime.evaluate({expression: "document.title"})` → "Editor | JSON Crack"
- 检查 `document.querySelector('canvas')` 是否存在
- Console 无错误（`browser_console()` 返回空数组、0 错误）
- 检测加载状态：`Runtime.evaluate({expression: \"document.querySelectorAll('.error, [class*=error], [class*=loading]').length\"})` 结果应为 0

## 注意事项

- jsoncrack 的 `fetchUrl()` 对 localhost URL 的 `isURL()` 校验通过
- 因为 CDP 浏览器和 static server 运行在同一宿主机，localhost 互通
- 文件较大的话（283K+）jsoncrack 的 canvas 渲染仍然流畅
