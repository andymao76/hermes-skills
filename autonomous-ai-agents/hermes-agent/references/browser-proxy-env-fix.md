# 代理环境变量对 Chromium 子进程的影响

## 问题描述

Hermes 所在的环境中设置了 `HTTP_PROXY`/`HTTPS_PROXY`/`ALL_PROXY` 等代理环境变量（用于访问被墙的 API 端点）。但 browser_tool 启动的 agent-browser 子进程会**继承这些环境变量**，导致 Chromium 的 DevTools Protocol 连接失败，报错：

```
net::ERR_NO_SUPPORTED_PROXIES
```

## 原因

Chromium 读取 `ALL_PROXY`、`HTTP_PROXY` 等环境变量作为系统代理配置。当环境中有 `ALL_PROXY=socks5://127.0.0.1:7897` 时，Chromium 尝试通过 SOCKS5 代理建立 DevTools Protocol WebSocket 连接，但该代理不支持或不处理这种连接模式。

即使设置 `--no-proxy-server` Chrome flag，如果 `ALL_PROXY` 或 `HTTPS_PROXY` 存在于环境中，仍然可能触发此错误。

## 修复

### 方案 1：修改 browser_tool.py（推荐，已验证）

在 `tools/browser_tool.py` 中两个 `browser_env = {**os.environ}` 位置，添加代理环境变量清理：

```python
browser_env = {**os.environ, "AGENT_BROWSER_SOCKET_DIR": task_socket_dir}
# Strip proxy env vars that break Chromium's network stack (gh #44712):
# Chromium reads HTTP_PROXY / ALL_PROXY from the environment, but
# Hermes needs these vars for its own API calls.  Removing them from
# the child env lets agent-browser use Chrome's own direct connection.
for _key in ("http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY",
             "ALL_PROXY", "all_proxy", "no_proxy", "NO_PROXY"):
    browser_env.pop(_key, None)
```

需要在两处添加：
1. `_run_tmp_session()` 函数（约第 860 行）——临时会话路径
2. `_run_browser_command()` 函数（约第 2001 行）——持久会话路径

### 方案 2：设置 AGENT_BROWSER_ARGS（不推荐，不彻底）

```bash
export AGENT_BROWSER_ARGS="--no-sandbox,--disable-dev-shm-usage,--no-proxy-server"
```

这个方法对 `ALL_PROXY` 和 `HTTPS_PROXY` 效果不稳定，且仍可能触发 `ERR_NO_SUPPORTED_PROXIES`。

## 验证方法

```bash
# 修改后验证
cd /home/andymao/.hermes/hermes-agent
source venv/bin/activate
python3 -c "
import sys; sys.path.insert(0, '.')
from tools.browser_tool import browser_navigate
result = browser_navigate('https://example.com', task_id='test')
print('SUCCESS' if '\"success\": true' in result else result[:200])
"
```

## 相关文件

- `~/hermes-agent/tools/browser_tool.py` — 两处 `browser_env` 构建
