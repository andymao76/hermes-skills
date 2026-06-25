# 知乎 MCP 服务器参考

> 源路径: `~/.hermes/mcp-servers/zh_mcp_server/`
> 上游项目: [Victorzwx/zh_mcp_server](https://github.com/Victorzwx/zh_mcp_server)

## 修改记录（适配本机 Linux 环境）

| 修改 | 原因 |
|------|------|
| `server.py` 中 `from .write_zhihu` → `from write_zhihu` | 相对导入在直接运行 `python3 server.py` 时失败 |
| `__init__.py` 中 `from . import server` → `import server` | 同上 |
| `__main__.py` 中 `from . import main` → `from server import main` | 同上 |
| `write_zhihu.py` 中 `_get_chrome_path()` 补充 snap chromium 路径 | Linux 下 snap chromium 在 `/snap/bin/chromium` |
| 创建 `run.py` 作为 stdio 入口（非 `-m` 方式） | 避免模块加载问题 |
| `pip install -e .` 从项目目录安装 | 确保 `mcp` 包可导入 |

## 工具

### `create_atticle(title, content, images=None, topic=None)`

发布文章到知乎。使用 Selenium + ChromeDriver 模拟浏览器操作。

- **title**: ≤100 字
- **content**: ≥9 字
- **images**: 本地图片路径（可选）
- **topic**: 话题（可选，不填则根据标题前4字符自动匹配）

## 登录

运行 `python3 ~/.hermes/mcp-servers/zh_mcp_server/login_manual.py`

这会打开浏览器窗口（非 headless），要求：
1. 手机号 + 密码登录
2. 如果触发验证码，在终端输入
3. Cookies 保存到 `zhihu_cookies.json`

## 安装命令

```bash
cd ~/.hermes/mcp-servers/zh_mcp_server
pip install -e .
```

注意：系统 `/usr/bin/python3` 无 `mcp` 包。必须用 venv python。

## 已知限制

- 基于 Selenium 模拟浏览器，速度较慢（~10秒/次发布）
- 依赖 ChromeDriver 版本匹配本地 Chrome
- Cookies 需要定期刷新
- 如果知乎页面结构变化，CSS selector 需要更新
