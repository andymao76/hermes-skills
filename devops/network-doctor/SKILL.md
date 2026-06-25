---
name: network-doctor
description: Hermes 网络与代理健康诊断 — 检测 Clash 端口、Provider 连通性、DNS 污染，输出修复建议和自动降级策略
trigger: 网络故障、代理异常、API 超时、Provider 不可用、翻墙失败、海外出差网络切换
category: devops
---

# Hermes 网络医生 (network-doctor)

## 快速诊断

```bash
bash ~/.hermes/skills/network-doctor/scripts/network_doctor.sh
```

## 适用场景

- Provider 返回超时/连接失败
- Web Search 工具无响应
- 海外出差切换网络
- 代理挂了但不知道
- DNS 污染导致 GitHub/Google 无法访问

## 诊断流程

### 1. 检查代理进程

```bash
# Clash Verge
ps aux | grep -E "clash-meta|mihomo|clash" | grep -v grep
ss -lntp | grep 7897

# 环境变量
env | grep -i proxy
```

期望:
- 进程运行中
- 端口 7897 LISTEN
- HTTP_PROXY=http://127.0.0.1:7897
- HTTPS_PROXY=http://127.0.0.1:7897
- 无 ALL_PROXY

### 2. 检查外网连通性

```bash
# Google（需代理）
curl -s -o /dev/null -w "%{http_code}" https://www.google.com --max-time 5

# GitHub
curl -s -o /dev/null -w "%{http_code}" https://github.com --max-time 5

# 国内
curl -s -o /dev/null -w "%{http_code}" https://www.baidu.com --max-time 5
```

### 3. 检查 Provider 连通性

```bash
# DeepSeek
curl -s -o /dev/null -w "%{http_code}" https://api.deepseek.com --max-time 5

# SiliconFlow
curl -s -o /dev/null -w "%{http_code}" https://api.siliconflow.cn --max-time 5

# Gemini
curl -s -o /dev/null -w "%{http_code}" https://generativelanguage.googleapis.com --max-time 5

# Nous
curl -s -o /dev/null -w "%{http_code}" https://inference-api.nousresearch.com --max-time 5
```

### 5. 检查 DNS（推荐 dig）

```bash
# DNS 污染检测
dig +short www.google.com
dig +short github.com
dig +short api.deepseek.com

# 或使用 host（兼容性更好）
host www.google.com 8.8.8.8 2>&1 | head -3
host api.deepseek.com 8.8.8.8 2>&1 | head -3
```

### 6. 直连 vs 代理延迟对比测试

诊断代理是否必须、代理是否正常工作，最佳方法是**同时测试代理和直连**：

```bash
# 一键对比（代理 vs 直连，自动输出延迟汇总表）
for site in "GitHub" "Google" "百度" "cnb.cool"; do
  case $site in
    GitHub) url="https://github.com";;
    Google) url="https://google.com";;
    百度)   url="https://www.baidu.com";;
    "cnb.cool") url="https://cnb.cool";;
  esac
  via_proxy=$(curl -s -o /dev/null -w "%{time_total}s" --max-time 10 "$url" 2>&1)
  direct=$(curl -s -o /dev/null -w "%{time_total}s" --noproxy '*' --max-time 10 "$url" 2>&1)
  echo "  $site: 代理=$via_proxy  直连=$direct"
done
```

预期结果解读：
- **Google 代理通、直连超时** → 代理正常工作，海外访问必须走代理
- **Google 两者都通** → 代理正常工作，也可直连
- **Google 两者都超时** → 网络断开或 DNS 污染
- **GitHub 直连慢(1.5s+)但代理快(0.3s)** → 代理加速效果明显

### 7. Git 远程连通性检查

针对 Hermes Agent 的 Git 仓库（origin/mirror 双源）：

```bash
cd ~/.hermes/hermes-agent
# 检查远程源
git remote -v

# 测试 GitHub 源
echo "--- origin (GitHub) ---"
git fetch origin main --dry-run 2>&1 | head -3

# 测试 cnb.cool 国内镜像
echo "--- mirror (cnb.cool) ---"
git fetch mirror main --dry-run 2>&1 | head -3
```

### 8. 代理进程详情

```bash
# 查看 Clash 进程详情
ps aux | grep -E "clash|mihomo" | grep -v grep

# 查看监听端口
ss -tlnp | grep -E "789[0-9]|909[0-9]"

# 检查 Clash 外部控制 API（如有配置）
curl -s --max-time 5 http://127.0.0.1:9090/version 2>/dev/null || echo "  Clash API 未配置"
```

## 网络模式切换（provider-switch 联动）

network-doctor 检测到网络不可用时，自动调用 provider-switch 降级：

| 检测结果 | 动作 |
|---------|------|
| Google 超时 + 百度正常 | 代理正常，Provider 切换国内（DeepSeek/SiliconFlow）|
| Google 正常 | 海外模式，Provider 切换 Gemini/OpenAI |
| 两者都超时 | 网络断开，输出修复命令 |
| 代理端口 7897 未 LISTEN | 清除 ALL_PROXY，降级国内直连 |

### 诊断结果汇总（推荐输出格式）

使用以下结构输出诊断报告，一目了然：

```text
=== 环境变量 ===
  HTTP_PROXY=http://127.0.0.1:7897/      ✅ 已设置
  SOCKS5 127.0.0.1:7898                  ❌ 不可达

=== DNS 解析 ===
  github.com → 20.205.243.166            ✅
  google.com → 173.194.203.101           ✅

=== 延迟对比 ===
  GitHub:  代理=0.35s  直连=1.53s        ✅ 代理加速
  Google:  代理=0.29s  直连=超时         ✅ 代理有效
  百度:    代理=0.14s  直连=0.21s        ✅
  cnb.cool:代理=0.53s  直连=0.51s        ✅

=== Git 远程 ===
  origin → github.com                    ✅ 正常
  mirror → cnb.cool                      ✅ 正常

=== Clash 进程 ===
  内核: verge-mihomo PID 4249              ✅ 运行中
  端口: 127.0.0.1:7897 LISTEN              ✅
```

```python
# Python 版汇总（适合在 Agent 回复中使用）
def report(results):
    status = "✅" if all(r["ok"] for r in results) else "❌"
    print(f"网络状态: {status}")
    for r in results:
        icon = "✅" if r["ok"] else "❌"
        print(f"  {icon} {r['name']}: {r['detail']}")
    if not all(r["ok"] for r in results):
        print(f"\n建议修复命令:")
        for r in results:
            if not r["ok"] and r.get("fix"):
                print(f"  {r['fix']}")
```

## 自动修复命令

### 重启代理
```bash
# Clash Verge (AppImage)
pkill clash-meta && ~/Applications/clash-verge.AppImage &
```

### 切换代理端口
```bash
export HTTP_PROXY=http://127.0.0.1:7897
export HTTPS_PROXY=http://127.0.0.1:7897
```

### 清除代理环境变量（紧急降级）
```bash
unset HTTP_PROXY HTTPS_PROXY ALL_PROXY http_proxy https_proxy
```

### 切换 DNS
```bash
# 写入临时 resolv
echo "nameserver 8.8.8.8" | sudo tee /etc/resolv.conf
```

## 故障判定表

| 现象 | 原因 | 处理 |
|------|------|------|
| Google 超时，百度正常 | 代理挂了 | 重启 Clash Verge |
| 所有 Provider 超时 | 网络断开 / DNS 污染 | 检查网卡 / 切换 DNS |
| DeepSeek 超时，Google 正常 | Provider 故障 | 切到 SiliconFlow |
| Gemini 超时，国内正常 | 代理问题 | 检查代理环境变量 |
| 部分 MCP 超时 | MCP 子进程代理未配置 | config.yaml 加 env.HTTP_PROXY |
| ALL_PROXY 错误 | SOCKS 配置冲突 | 清除 ALL_PROXY |
| **Google/YouTube/Twitter 正常，但 chatgpt.com / api.openai.com 全部 HTTP 000** | **代理节点 IP 被 OpenAI/Cloudflare 屏蔽** | 见下方「OpenAI 被屏蔽专项」 |
| 云服务器 SSH 超时 | 安全组规则误删 | 去云控制台恢复 22 端口入站规则 |
| 云服务器 80 端口不通 | 安全组未开放 HTTP | 添加入站规则 TCP 80 |
| SSH 隧道 `GatewayPorts` 不生效 | sshd_config 未开启 | `sudo sed -i 's/#GatewayPorts no/GatewayPorts yes/' /etc/ssh/sshd_config && sudo systemctl restart sshd` |

### OpenAI/ChatGPT 被代理节点屏蔽专项

**特征：** 代理服务正常运行（Google/YouTube/Twitter 均正常），但所有 OpenAI 域名（chatgpt.com、api.openai.com、chat.openai.com、cdn.oaistatic.com、platform.openai.com）均返回 HTTP 000（连接失败），延迟通常在 0.3~0.6s（说明连接被快速拒绝而非超时）。

**原因：** 代理服务商的出口 IP 被 OpenAI/Cloudflare 屏蔽。这是常见问题——OpenAI 严格封禁数据中心 IP，多数机场/代理节点的 IP 段都在黑名单中。

**诊断方法：**
```bash
# 1. 确认代理正常工作
curl -s -o /dev/null -w "google: %{http_code}\n" --proxy http://127.0.0.1:7897 https://www.google.com

# 2. 测试 OpenAI 多个域名
for url in https://chatgpt.com https://api.openai.com https://chat.openai.com; do
  echo "$url → $(curl -s -o /dev/null -w '%{http_code}' --proxy http://127.0.0.1:7897 --max-time 5 $url)"
done

# 3. 检查不同区域节点（TW 节点可能返回 403 而非 000，说明可连接但被拒）
curl -s --unix-socket /tmp/verge/verge-mihomo.sock -X PUT http://localhost/proxies/OpenAI \
  -H "Content-Type: application/json" -d '{"name":"TW自动选择"}' 2>/dev/null
# 切换后再测 chatgpt 看是否从 000 变为 403/其他状态码

# 4. （推荐）批量扫描所有策略组 —— 一键找出哪些区域返回 403（能连上）而非 000（被RST杀）
for group in "自动选择" "负载均衡" "HK自动选择" "JP自动选择" "KR自动选择" "SG自动选择" "TW自动选择" "US自动选择"; do
  curl -s --unix-socket /tmp/verge/verge-mihomo.sock \
    -X PUT http://localhost/proxies/OpenAI \
    -H "Content-Type: application/json" \
    -d "{\"name\":\"$group\"}" &>/dev/null
  sleep 0.3
  code=$(curl -s -o /dev/null -w "%{http_code}" -x http://127.0.0.1:7897 \
    --max-time 5 https://chatgpt.com 2>/dev/null)
  echo "$group → HTTP $code"
done
```

**输出解读：**
- **HTTP 000** = 连接被 TCP RST 杀死 —— IP 段被 OpenAI/Cloudflare 完全封杀
- **HTTP 403** = 连接已到达 OpenAI 服务器，但被 Cloudflare WAF 拦截 —— 比 000 好，说明 IP 未被彻底封杀
- 多个区域都是 000 → 大概率换订阅商才能解决
- 至少有一个区域返回 403 → 优先固定该区域，后续可尝试加浏览器 User-Agent / Accept 头绕过 WAF

#### 进阶：批量测试所有单个节点（而非策略组）

策略组扫描只能看出「哪个区域还能连上」，但无法回答「具体哪个节点能用」。同一区域的不同节点 IP 段可能不同，屏蔽状态也不同（如 US-1TCP 出 403 而 US-2TCP~5TCP 全 000）。需要降到**单个节点**级别测试。

**原理：**
1. 将 OpenAI 策略组指向「主代理」（让 ChatGPT 流量走 主代理 选中的节点）
2. 遍历 主代理 策略组下的所有单个节点，逐一切换并测试 Google + ChatGPT
3. 用 Clash unix socket API 切换节点，用 curl --proxy 测试目标

**完整测试脚本在 `scripts/batch_test_nodes.py`，用法：**
```bash
python3 ~/.hermes/skills/devops/network-doctor/scripts/batch_test_nodes.py
```

**关键实现逻辑（供参考）：**
```bash
# 1. 先让 OpenAI 流量走主代理
curl -s --unix-socket /tmp/verge/verge-mihomo.sock \
  -X PUT http://localhost/proxies/OpenAI \
  -H "Content-Type: application/json" \
  -d '{"name":"主代理"}'

# 2. 获取所有节点列表（非策略组）
curl -s --unix-socket /tmp/verge/verge-mihomo.sock \
  http://localhost/proxies | python3 -c "
import json,sys; d=json.load(sys.stdin); skiptypes={'Selector','URLTest','Fallback','LoadBalance','Relay','Direct','Reject','Compatible','Pass','RejectDrop'}
print('\n'.join(k for k,v in d['proxies'].items() if v['type'] not in skiptypes))
"

# 3. 测试单个节点
node="US-1TCP"
curl -s --unix-socket /tmp/verge/verge-mihomo.sock \
  -X PUT "http://localhost/proxies/%E4%B8%BB%E4%BB%A3%E7%90%86" \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"$node\"}" &>/dev/null
sleep 0.3
echo "Google=$(curl -s -o /dev/null -w '%{http_code}' --proxy http://127.0.0.1:7897 --max-time 5 https://www.google.com)"
echo "ChatGPT=$(curl -s -o /dev/null -w '%{http_code}' --proxy http://127.0.0.1:7897 --max-time 5 https://chatgpt.com)"
```

**实测发现：**
- Hysteria2 (HY2) 节点延迟最低（0.2~0.5s），且更可能返回 403（连上服务器）而非 000（被杀）
- 同一区域内 Vless 节点往往全 000，而 HY2 节点有概率出 403
- 没有任何节点返回 HTTP 200 时，说明机场的整个 IP 池都被封了，需换订阅商

**解决方法（由易到难）：**
1. **切换备用订阅** — 在 Clash Verge 界面切换到另一个订阅（如 CrossWall 等有美国 Cloudflare ECH 节点的服务商）
2. **更新订阅获取新节点** — 在 Clash Verge 中右键当前订阅 → 更新，可能换到未被屏蔽的 IP
3. **使用 Clash Verge 内置 OpenAI 策略组** — 尝试切换到 US 自动选择 / 自动选择 / 负载均衡 等不同组
4. **检查规则集** — 确认 OpenAI-Site.mrs / OpenAI-IP.mrs 规则集是否正常更新
5. **改用它路** — 如果只是为了调用 API，可临时切换到 SiliconFlow 或 DeepSeek 等国内可直连的提供商

**Clash 规则查看方法：**
```bash
# 使用 Unix socket 查看当前选中节点
curl -s --unix-socket /tmp/verge/verge-mihomo.sock http://localhost/proxies/OpenAI

# 检查规则集文件
ls -la ~/.local/share/io.github.clash-verge-rev.clash-verge-rev/ruleset/OpenAI-*
```

## 参考文档

| 文档 | 内容 |
|------|------|
| `references/discord-channel-diagnostics.md` | Discord Bot 连通性、Home Channel 配置同步、Gateway 重启、发送测试 |
| `references/ssh-reverse-tunnel-proxy.md` | SSH 反向隧道 + Nginx 反向代理将本地服务暴露到公网（含腾讯云安全组配置） |
| `references/full-diag.sh` | 一键全量诊断脚本 — 代理端口/DNS/延迟对比/Git 远程/Clash进程，输出汇总 |
| `scripts/batch_test_nodes.py` | 批量测试 Clash 所有单个节点对 OpenAI 等目标的连通性（按节点/IP级别逐测） |
