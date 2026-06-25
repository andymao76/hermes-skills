---
name: network-proxy-diagnostics
description: "Ubuntu 24.04 网络代理与连接诊断 — 检查代理环境变量、DNS 解析、端口、外网连通性（代理与直连对比）、Git 远程连通性、Python 网络、Hermes 状态，并提供标准修复流程和故障判定速查表"
trigger: 当 Hermes 出现网络相关错误时使用，包括：Check network connectivity、Unknown scheme for proxy URL、API call failed、Connection timeout、Nous Portal login failed、DeepSeek/OpenAI/Qwen API 无法访问、WhatsApp Bridge 无法联网
category: devops
---

# 网络代理与连接诊断（Ubuntu 24）

## 适用场景

当 Hermes 出现以下问题时使用：
- `Check network connectivity`
- `Unknown scheme for proxy URL`
- `API call failed`
- `Connection timeout`
- Nous Portal login failed
- DeepSeek / OpenAI / Qwen API 无法访问
- WhatsApp Bridge 无法联网

---

## 一、检查代理环境变量

查看当前代理配置：

```bash
env | grep -i proxy
```

### 推荐配置

```bash
export HTTP_PROXY=http://127.0.0.1:7897
export HTTPS_PROXY=http://127.0.0.1:7897
export NO_PROXY=localhost,127.0.0.1,::1
```

### 错误配置（建议删除）

```bash
export ALL_PROXY=socks://127.0.0.1:7897
export all_proxy=socks://127.0.0.1:7897
```

**说明**：部分 Python、HTTPX、Hermes Provider 会因为 SOCKS URL 解析问题出现 `Unknown scheme for proxy URL`。

---

## 二、检查代理端口

确认代理程序运行：

```bash
ss -lntp | grep 7897
```

正常结果：
```
LISTEN 0 4096  127.0.0.1:7897
```

检查代理程序：

```bash
ps -ef | grep -E "clash|mihomo|sing-box|xray"
```

---

## 三、检查外网连接

测试 Google：

```bash
curl -I https://www.google.com
```

正常返回：
```
HTTP/2 200
```

---

## 四、检查 DeepSeek 连通性

```bash
curl -I https://api.deepseek.com
```

正常返回：
```
HTTP/2 401
```

**说明**：
- 网络正常
- API 可达
- 未认证属于正常现象，不要误判为网络故障。

---

## 五、检查 Nous Portal 连通性

```bash
curl -I https://inference-api.nousresearch.com/v1
```

可能返回：
```
HTTP/2 404
```

**说明**：
- 域名可访问
- API 服务在线
- 根路径返回 404 属正常现象。

---

## 六、检查 Python 网络

Hermes 基于 Python 运行，测试：

```bash
python3 - <<'EOF'
import requests

r = requests.get(
    "https://www.google.com",
    timeout=10
)

print(r.status_code)
EOF
```

正常结果：
```
200
```

---

## 七、检查 Hermes 状态

```bash
# 查看诊断信息
hermes doctor

# 查看详细信息
hermes doctor --verbose

# 查看 Provider
hermes status

# 查看全部配置
hermes config list
```

---

## 八、清理代理缓存

1. 编辑 `~/.bashrc`
2. 删除以下行（如果存在）：
   - `ALL_PROXY`
   - `all_proxy`
3. 刷新：`source ~/.bashrc`
4. 重新打开终端。

---

## 九、标准修复流程

按顺序执行：

| 步骤 | 命令 | 验证 |
|------|------|------|
| 1 | `env \| grep -i proxy` | HTTP_PROXY / HTTPS_PROXY 存在，无 ALL_PROXY |
| 2 | `ss -lntp \| grep 7897` | LISTEN 状态 |
| 3 | `curl -I https://www.google.com` | HTTP/2 200 |
| 4 | `curl -I https://api.deepseek.com` | HTTP/2 401 |
| 5 | `python3 network_test.py` | 200 |
| 6 | `hermes doctor` | 正常 |
| 7 | `hermes status` | 正常 |
| 8 | `hermes config list` | 配置完整 |

---

## 十、故障判定速查表

| 现象 | 原因 | 处理 |
|------|------|------|
| `Unknown scheme for proxy URL` | ALL_PROXY 配置错误 | 删除 ALL_PROXY |
| curl Google 失败 | 代理未启动 | 启动 Clash / Mihomo |
| DeepSeek 返回 401 | 未认证 | 正常现象 |
| Nous 返回 404 | 根路径访问 | 正常现象 |
| Hermes Doctor 网络失败 | Provider 检测异常 | 查看 `hermes status` |
| API 401 | Key 无效 | 重新配置 |
| API 429 | 配额耗尽 | 充值或更换 Provider |
| Connection Timeout | 网络问题 | 检查代理 |
| WhatsApp Bridge Code 408 | Baileys WebSocket 直连失败（国内网络） | 见 `hermes-whatsapp-bridge` 技能：给 bridge.js 加 `https-proxy-agent` |

---

## 最终结论

满足以下条件即可判定网络正常：

- [x] `HTTP_PROXY` 存在
- [x] `HTTPS_PROXY` 存在
- [x] 无 `ALL_PROXY`
- [x] Google 返回 200
- [x] DeepSeek 返回 401
- [x] Python requests 返回 200
- [x] `hermes status` 正常

此时问题通常不是网络，而是：
- API Key 无效或缺失
- Provider 配置错误
- 模型配置不匹配
- Hermes Bug
- 配额不足

---

---

## 十一、DNS 解析诊断

```bash
for host in "github.com" "google.com" "baidu.com" "cnb.cool"; do
  result=$(dig +short "$host" 2>/dev/null | head -3 || \
           nslookup "$host" 2>/dev/null | grep "Address:" | tail -1 || echo "  FAIL")
  echo "  $host → $result"
done
```

DNS 故障时 curl/git 会报 `Could not resolve host`，即使代理端口正常也无法上网。

---

## 十二、外网连通性对比（代理 vs 直连）

同时测代理和直连，对比延迟：

```bash
# 代理方式
curl -s -o /dev/null -w "%{http_code} (%{time_total}s)" --max-time 10 "https://github.com"

# 直连方式（绕过代理）
curl -s -o /dev/null -w "%{http_code} (%{time_total}s)" --noproxy '*' --max-time 10 "https://github.com"
```

**对比判定表：**

| 代理结果 | 直连结果 | 结论 |
|---------|---------|------|
| 正常 | 正常 | 整体网络正常，问题在应用层 |
| 正常 | 超时 | 正常（被封锁），必须走代理 |
| 超时 | 正常 | 代理配置/节点问题 |
| 都超时 | 都超时 | 系统网络问题或 DNS 故障 |

---

## 十三、Hermes Git 远程连通性（hermes update 排障）

当 `hermes update` 失败时，先确认运行目录是否在 Hermes git 仓库中：

```bash
# 确认 Hermes 安装路径
which hermes
ls -la $(which hermes)

# Hermes 实际在 ~/.hermes/hermes-agent/ 下
cd ~/.hermes/hermes-agent

# 查看远程源（通常有 origin + mirror 两个）
git remote -v

# 测试 fetch
git fetch origin main --dry-run 2>&1
git fetch mirror main --dry-run 2>&1   # 如有国内镜像

# 检查是否有新提交
git rev-list HEAD..origin/main --count
```

### Git TLS 错误速查

| 错误信息 | 根因 | 措施 |
|----------|------|------|
| `gnutls_handshake() failed: The TLS connection was non-properly terminated` | 临时网络抖动 / 代理节点切换 | **重试即可**，一般立即恢复 |
| `Could not resolve host: github.com` | DNS 故障或代理断开 | 检查 DNS + Clash 进程 |
| `Authentication failed` | git 凭据过期 | 检查 SSH key / git credentials |
| `fatal: not a git repository` | 在非 git 目录执行 | cd 到 `~/.hermes/hermes-agent` 再执行 |
| `Failed to fetch updates from origin` | 网络不通 | 执行本节诊断流程 |

---

## 十四、Clash Verge 进程详情

```bash
# 进程
ps aux | grep -i clash | grep -v grep

# 监听端口（区分 HTTP/SOCKS）
ss -tlnp 2>/dev/null | grep -E "789[0-9]|9090"

# SOCKS5 端口可能和 HTTP 同口，也可能分开
timeout 3 bash -c 'echo > /dev/tcp/127.0.0.1/7897' 2>/dev/null && echo "HTTP 7897 可达" || echo "HTTP 7897 不可达"
timeout 3 bash -c 'echo > /dev/tcp/127.0.0.1/7898' 2>/dev/null && echo "SOCKS5 7898 可达" || echo "SOCKS5 7898 不可达"
```

### 常见 Clash 组件

| 组件 | 说明 |
|------|------|
| `clash-verge` | Clash Verge UI 主进程 |
| `verge-mihomo` | Clash Meta 内核（替换原 clash） |
| `clash-meta` | 另一种内核实现 |
| `7897` | HTTP/SOCKS5 混合代理端口（常用） |
| `7898` | 纯 SOCKS5 代理端口（可能不开放） |
| `9090` | 外部控制 API（可能为 Unix Socket） |

---

## 十五、输出诊断报告模板

```markdown
## 诊断结论
| 项 | 状态 | 说明 |
|----|------|------|
| 代理服务 | ✅/❌ | Clash Verge 运行状态 |
| DNS 解析 | ✅/❌ | 域名能否正确解析 |
| 外网访问（代理） | ✅/❌ | GitHub/Google 通过代理可达 |
| 直连环境 | ⚠/✅ | 是否需要代理 |
| Git 远程源 | ✅/❌ | origin/mirror 拉取状态 |
| Python requests | ✅/❌ | Hermes 底层网络栈 |
```

---

## 参考

- `references/knowledge-base-sync.md` — 知识文件同步说明
- `~/knowledge/Hermes/network_proxy_diagnosis_skill.md` — 知识库镜像副本
- `hermes-system-maintenance` — 高级代理配置（NO_PROXY 分流、systemd proxy.conf）
- `network-doctor` — 更详细的网络排障技能
