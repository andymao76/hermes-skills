# Selenium MCP Server 部署指南

适用于需要浏览器自动化的内容平台 MCP Server（知乎、掘金等）。

## 环境检查

```bash
# 检查 Chrome/Chromium
which chromium || which google-chrome || which chromium-browser

# 检查 chromedriver（snap chromium 自带）
/snap/chromium/*/usr/lib/chromium-browser/chromedriver --version

# 检查 Selenium 可用
pip list 2>/dev/null | grep selenium
```

## 依赖安装

```bash
pip install selenium requests mcp webdriver-manager
```

## Snap Chromium 注意事项

**如果系统使用 snap 版 Chromium（常用在 Ubuntu）：**

1. Selenium 会自动尝试多种初始化方式（`_init_with_default`, `_init_with_service`, `_init_with_webdriver_manager` 等）
2. 确保代码的 `_get_chrome_path()` 方法能发现 snap chromium：
   ```python
   # Linux 下检测路径
   for cmd in ["google-chrome", "google-chrome-stable", "chromium-browser", "chromium"]:
       path = subprocess.check_output(["which", cmd]).decode().strip()
   # snap 路径
   "/snap/bin/chromium"
   ```
3. snap chromium 启动 headless 模式较慢，connect_timeout 建议设 30s+

## 项目结构

```
~/.hermes/mcp-servers/<platform>/
├── __init__.py         # 包入口
├── __main__.py         # python -m 入口
├── server.py           # FastMCP 服务器
├── write_<platform>.py # Selenium 操作封装
├── login_manual.py     # 手动登录脚本
├── data/               # cookies 存储目录
├── requirements.txt
└── pyproject.toml      # 可选，用于 pip install -e
```

## 常见坑点

### 1. 相对导入错误
Selenium 封装类通常用 `from .write_xxx import Xxx` 相对导入。
**改为绝对导入**降低模块路径问题：
```python
# 将 from .write_zhihu import ZhuHuPoster 改为
from write_zhihu import ZhuHuPoster
```
配合启动脚本：
```python
#!/usr/bin/env python3
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from server import mcp
mcp.run()
```

### 2. Python 路径问题
**Hermes 的 MCP server 使用系统 python（`/usr/bin/python3`）**，但依赖装在 venv 里会导致 ModuleNotFoundError。

**解决**：config.yaml 中 command 必须指向 venv 的 python：
```yaml
mcp_servers:
  zhihu:
    command: /home/andymao/.hermes/hermes-agent/venv/bin/python3  # 不是 /usr/bin/python3
    args: ["/path/to/run.py"]
```

查看 venv python 路径：
```bash
which python3
```

### 3. Headless 模式首次启动慢
Selenium headless 模式首次启动可能需要 5-10 秒。
- `connect_timeout` 设 30s+
- 如果 `hermes mcp test` 返回 "Connection closed"，先用 stdio 测试：
  ```bash
  echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{...}}' | timeout 10 python3 run.py
  ```
  看是否能收到 JSON-RPC 响应。

### 4. 登录需要交互
Selenium 模式的 MCP server 通常需要手动登录保存 cookies：
```bash
cd ~/.hermes/mcp-servers/<platform> && python3 login_manual.py
```
登录脚本应使用 `headless=False` 弹出浏览器窗口。

Cookies 文件位置：
- 默认在包目录下（`zhihu_cookies.json`）
- 可通过环境变量 JSON_PATH 指定目录

### 5. MCP test 通过但运行时失败
- 检查 `hermes mcp list` 是否显示 server
- 检查 `~/.hermes/logs/agent.log` 中对应 server 的连接日志
- `hermes mcp test` 用 CLI 路径测试，`hermes mcp list` 读 config.yaml
- 如果 test 成功但运行时失败，可能是 transport 状态缓存问题，需重启 Hermes

## 验证流程

```bash
# 1. 本地测试 MCP 初始化
cd ~/.hermes/mcp-servers/<platform> && python3 -c "
import sys; sys.path.insert(0, '.')
from server import mcp
print('OK:', mcp.name)
"

# 2. 测试单个工具
python3 -c "
import sys; sys.path.insert(0, '.')
from server import some_tool
print(some_tool('test'))
"

# 3. Hermes MCP test
hermes mcp test <platform>

# 4. 查看日志
grep -i '<platform>' ~/.hermes/logs/agent.log

# 5. 重启 Hermes 后使用
/reload-mcp
```
