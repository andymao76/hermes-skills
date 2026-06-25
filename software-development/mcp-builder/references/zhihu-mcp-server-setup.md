# 知乎 MCP Server 安装配置指南（Selenium 模式）

用了 Victorzwx/zh_mcp_server（Selenium + ChromeDriver 模拟浏览器发文章）。

## 安装步骤

### 1. 克隆项目

```bash
git clone --depth=1 https://github.com/Victorzwx/zh_mcp_server.git
```

### 2. 安装依赖

```bash
pip install selenium requests mcp webdriver-manager
```

### 3. 放置到 mcp-servers 目录

```bash
mkdir -p ~/.hermes/mcp-servers/zh_mcp_server
cp -r /tmp/zh_mcp_server/* ~/.hermes/mcp-servers/zh_mcp_server/
```

### 4. 修复 Linux 上的 Chrome 路径

项目 `write_zhihu.py` 的 `_get_chrome_path()` 方法只搜 `google-chrome` 命令，
在 Ubuntu 上系统安装的是 `chromium`（snap 版），需要扩展为：

```python
def _get_chrome_path(self):
    # ... 原有代码 ...
    elif system == "Linux":
        for cmd in ["google-chrome", "google-chrome-stable", "chromium-browser", "chromium"]:
            try:
                path = subprocess.check_output(["which", cmd]).decode().strip()
                if path: return path
            except: continue
        snap_path = "/snap/bin/chromium"
        if os.path.exists(snap_path): return snap_path
        return None
```

### 5. 修复相对导入

项目原本用 `from .write_zhihu import ...` 的相对导入，
但直接运行时 Python 无法解析。修复方式：

- 修改 `server.py`：`from .write_zhihu` → `from write_zhihu`
- 修改 `__init__.py`：`from . import server` → `import server`
- 修改 `__main__.py`：`from . import main` → `from server import main`

### 6. 创建 run.py 启动入口

```python
#!/usr/bin/env python3
import sys, os
server_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, server_dir)
from server import mcp
mcp.run()
```

### 7. Python 路径陷阱

**必须使用 venv 的 python**，而非系统 python：

```yaml
# config.yaml
mcp_servers:
  zhihu:
    command: /home/andymao/.hermes/hermes-agent/venv/bin/python3  # ✅
    args: ["/home/andymao/.hermes/mcp-servers/zh_mcp_server/run.py"]
    connect_timeout: 30
    timeout: 120
    env:
      json_path: /home/andymao/.hermes/mcp-servers/zh_mcp_server/data
```

## 登录

必须手动登录获取 cookies。创建 `login_manual.py`：

```python
from write_zhihu import ZhuHuPoster
poster = ZhuHuPoster('data', headless=False)  # 非 headless 模式
poster.login()
poster.close()
```

运行后浏览器会弹出，用手机号+验证码登录，cookies 自动保存到 `zhihu_cookies.json`。

## 验证

```bash
hermes mcp test zhihu
# → ✓ Connected / ✓ Tools discovered: 1 (create_atticle)
```

## 已知问题

- 只暴露一个工具 `create_atticle`（发布文章到知乎），没有搜索/读取功能
- Selenium 模式依赖桌面环境（headless 模式在某些 Linux 上不稳定）
- snap 版 chromium 启动慢，headless 超时风险高
