# Provider Proxy & Latency Matrix

Environment: Linux (Ubuntu 24.04), Clash proxy at 127.0.0.1:7897
Date: 2026-06-08 (initial + proxy audit)

## Test Results

| Provider | Endpoint | Proxy Needed? | Latency Direct | Latency via Proxy | Status |
|----------|----------|--------------|----------------|-------------------|--------|
| DeepSeek | api.deepseek.com/v1 | No | 300-530ms | 140-360ms | ✅ OK |
| SiliconFlow 国际 | api.siliconflow.com/v1 | **Yes** (slow direct) | 1312ms | **862ms** | ✅ OK |
| SiliconFlow 国内 | api.siliconflow.cn/v1 | No | **185-235ms** | 147-324ms | ✅ OK (preferred) |
| 阿里百炼 | dashscope.aliyuncs.com/v1 | No | **216-470ms** | 182-374ms | ✅ OK, 212 models |
| Gemini 2.5-flash | generativelanguage.googleapis.com | **Yes** (GFW blocked) | blocked | 1299ms | ✅ OK |
| OpenRouter | openrouter.ai/api/v1 | Yes | 261ms | 1633ms | ✅ OK (after key fix) |
| 微信 API | ilinkai.weixin.qq.com | No | **167-233ms** | 186ms | ✅ OK |

## Key Observations

### Proxy Rules
- **Must proxy**: Gemini (both models, direct connection blocked by GFW), SiliconFlow 国际, OpenRouter
- **No proxy needed (domestic)**: SiliconFlow 国内, 阿里百炼 (DashScope), DeepSeek, 微信 API

## Proxy Configuration for Hermes

### systemd proxy.conf (gateway + bridge)

Hermes gateway 和 bridge 的代理环境变量通过 systemd override 文件注入：

```ini
# ~/.config/systemd/user/hermes-gateway.service.d/proxy.conf
[Service]
Environment=HTTPS_PROXY=http://127.0.0.1:7897
Environment=HTTP_PROXY=http://127.0.0.1:7897
Environment=NO_PROXY=localhost,127.0.0.1,::1,.local,.aliyuncs.com,.siliconflow.cn,.deepseek.com,.weixin.qq.com,.wechat.com,.xiaohongshu.com,.zhihu.com,.taobao.com,.tmall.com,.csdn.net,.baidu.com,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16
```

**bridge 进程必须单独配置** — bridge 的 service.d 目录可能不存在，需要手动创建并复制 proxy.conf。

### Shell vs systemd NO_PROXY 差异

shell 和 systemd 的 NO_PROXY 可能不同，需分别验证：

```bash
echo "Shell NO_PROXY=$NO_PROXY"
echo "Gateway NO_PROXY=$(cat /proc/$(systemctl --user show hermes-gateway --property=MainPID | cut -d= -f2)/environ | tr '\0' '\n' | grep ^NO_PROXY | cut -d= -f2)"
```

**典型差异**: shell 可能有完整 CIDR（192.168/10/172.16），但 systemd proxy.conf 只有最小配置。

### NO_PROXY 域名匹配规则

格式 `NO_PROXY=.example.com` 匹配 `api.example.com` 和 `sub.api.example.com`。逗号分隔。不支持通配符 `*`（特殊上下文除外）。

### MCP Server Proxy Independence

| MCP Server | Proxy Setting | Location | Notes |
|-----------|--------------|----------|-------|
| wikipedia-mcp | `HTTPS_PROXY: 127.0.0.1:7897` | Foreign | Config.yaml env 独立设置 |
| taobao-mcp | `NO_PROXY: '*'` | Chinese | 显式绕过所有代理 |
| xiaohongshu-mcp | 未设（继承系统） | Chinese | 建议显式设置 |
| zhihu/csdn-mcp | 未设（继承系统） | Chinese | 建议显式设置 |

## Verification Method: Socket Hook

Use this to confirm whether a URL actually connects to the proxy or direct:

```python
import os, socket, urllib.request

os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7897'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7897'
os.environ['NO_PROXY'] = 'localhost,127.0.0.1,::1,.local,.aliyuncs.com,.siliconflow.cn,.deepseek.com'

original = socket.create_connection
tracked = {}

def hook(address, *a, **kw):
    tracked['dest'] = address
    raise Exception('abort')
socket.create_connection = hook

try:
    urllib.request.urlopen('https://api.siliconflow.cn', timeout=3)
except:
    pass

is_proxy = tracked.get('dest') and tracked['dest'][0] == '127.0.0.1'
print('走代理' if is_proxy else '直连', tracked.get('dest'))
```

## Recommended Provider Priority

1. **SiliconFlow 国内站** (fastest, no proxy, 93 models)
2. **阿里百炼** (fast, domestic, 212 models)
3. **SiliconFlow 国际站** (fallback, needs proxy, ~862ms)
4. **Gemini 2.5-flash** (translations, auxiliary tasks, needs proxy)
5. **DeepSeek** (domestic, ~250ms)
6. **OpenRouter** (many models, needs proxy, ~1633ms)
