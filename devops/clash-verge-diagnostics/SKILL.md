---
name: clash-verge-diagnostics
description: 诊断 Clash Verge 代理状态——检查进程、端口、订阅、节点连通性，定位 Telegram/Discord 推送失败根因
category: devops
tags: [proxy, clash-verge, network, telegram, discord, vpn, diagnostics]
related_skills: [hardware-diagnostics, incident-commander]
---

# Clash Verge 代理诊断

诊断 Clash Verge（clash-verge-rev / verge-mihomo）代理的运行状态，定位 Telegram、Discord、API 调用等依赖代理出境的推送失败根因。

## 触发场景

- Telegram / Discord 消息推送失败（`httpx.ConnectError`）
- 代理端口 7897 在监听但无法连通外网
- Clash Verge 进程运行正常但节点全红
- 用户反馈"翻墙连不上"
- Cron 任务中推送目标为 telegram/discord 时持续报错

## 配置路径

Clash Verge 配置文件目录：
```
~/.local/share/io.github.clash-verge-rev.clash-verge-rev/
```

关键文件：
| 文件 | 用途 |
|------|------|
| `verge.yaml` | Clash Verge 程序设置（TUN模式、系统代理、外部控制器等） |
| `profiles.yaml` | **订阅列表**（UID、URL、流量用量、到期时间、当前选中节点） |
| `clash-verge.yaml` | 运行时生成的 mihomo 完整配置 |
| `logs/clash.log` | mihomo 运行日志 |

`profiles.yaml` 中的关键字段（read_file 安全读取）：
- `current` — 当前激活的订阅 UID
- `items[].type: remote` — 远程订阅项
- `url` — 订阅链接
- `selected[].now` — 当前选中的代理节点
- `extra.upload/download/total` — 流量统计（字节）
- `extra.expire` — 到期 Unix 时间戳
- `updated` — 最后更新时间戳

## 诊断步骤

### 1. 检查进程是否运行

```bash
ps aux | grep -E 'clash|verge|mihomo' | grep -v grep
```

预期看到 3 个进程：
- `clash-verge` — GUI 进程
- `clash-verge-service` — 后端服务
- `verge-mihomo` — 核心代理引擎

### 2. 检查代理端口监听

```bash
ss -tlnp | grep 7897
```

或查看 verge-mihomo 进程的所有监听端口：
```bash
ss -tlnp | grep verge-mihomo
```

端口对照：
| 端口 | 用途 |
|------|------|
| 7897 | HTTP/SOCKS5 混合代理（主力） |
| 7895 | Verge 重定向端口 |
| 7896 | TProxy 端口 |
| 7898 | SOCKS5 端口 |
| 7899 | HTTP 端口 |

### 3. 读取订阅信息（安全方式）

用 `read_file` 读取 profiles.yaml（避免终端被安全策略拦截）：

```bash
~/.local/share/io.github.clash-verge-rev.clash-verge-rev/profiles.yaml
```

重点关注：
- **流量余量**：`extra.upload/download/total` — 单位字节，换算 GB = 值 / 1073741824
- **到期时间**：`extra.expire` — Unix 时间戳，用 `date -d @<timestamp>` 换算
- **当前节点**：每个 group 的 `selected[].now` 字段
- **最后更新**：`updated` 字段，确认订阅是否过期未刷新

### 4. 检查 verge 设置（外部控制器等）

```bash
~/.local/share/io.github.clash-verge-rev.clash-verge-rev/verge.yaml
```

关键字段：
- `enable_external_controller` — 是否启用外部 API（false 则无法用 HTTP API 切换节点）
- `enable_tun_mode` — TUN 模式
- `enable_system_proxy` — 系统代理设置

### 5. 测试代理连通性

```bash
curl -v --connect-timeout 8 --proxy http://127.0.0.1:7897 http://www.gstatic.com/generate_204
```

预期返回 HTTP 204（空响应体）。如果超时或者 000 说明节点不通。

备用测试地址：
- `http://cp.cloudflare.com/generate_204`
- `https://www.google.com`
- `https://api.telegram.org`

### 6. 查看 mihomo 日志

```bash
cat ~/.local/share/io.github.clash-verge-rev.clash-verge-rev/logs/clash.log | tail -20
```

搜索错误关键词：
- `error` — 连接错误
- `timeout` — 超时
- `dial` — 拨号失败
- `proxy` — 代理相关错误

### 7. 检查 verge-mihomo 服务状态

```bash
journalctl -u clash-verge-service --no-pager -n 20
```

## 常见诊断结论

### 情况 A：进程运行、端口监听、但节点不通
**原因**：当前选中节点（如 JP-1）服务器端挂了或网络波动
**处理**：
- 开 Clash Verge GUI 手动切换节点
- 切换到另一个订阅的节点（如 CrossWall）
- 更新订阅刷新节点列表
- 如频繁断连，更换订阅

### 情况 B：进程和端口都正常，流量也有余额
**原因**同上，节点线路问题而非订阅过期

### 情况 C：流量用尽或过期
**处理**：更新订阅或购买新套餐

### 情况 D：外部控制器未启用，无法远程切节点
`verge.yaml` 中 `enable_external_controller: false`
**处理**：手动开 GUI -> 设置 -> 开启外部控制器（端口 9097），或直接改 verge.yaml

## 典型 profiles.yaml 解读

```yaml
current: RzAmHuEvNuOC              # 当前激活的订阅 UID
items:
- uid: RzAmHuEvNuOC
  type: remote
  name: Basic-677806               # 订阅名称
  url: https://app.mitce.net/...   # 订阅链接
  selected:                        # 各组当前节点
  - name: GLOBAL                   # 全局组
    now: JP-1                      # 当前节点
  extra:
    upload: 1611671817             # 上传量（字节 ≈ 1.5GB）
    download: 21482324728          # 下载量（字节 ≈ 20GB）
    total: 107374182400            # 总量（字节 = 100GB）
    expire: 1787328000             # 到期时间（Unix时间戳）
  updated: 1781053691              # 最后更新时间
```

## 恢复 Telegram/Discord 推送

代理连通性验证：
```bash
curl -s --connect-timeout 8 --proxy http://127.0.0.1:7897 -o /dev/null -w '%{http_code}' https://api.telegram.org
```

返回 `200` 则代理正常。

### Hermes Gateway 平台恢复（断连后）

当 Telegram 或 Discord 连续失败 10 次后，Gateway 会暂停该平台：

```bash
# 检查暂停状态
grep "paused after" ~/.hermes/logs/gateway.log | tail -5
```

典型日志：`discord paused after 10 consecutive failures (discord connect timed out after 30s)`

恢复方法：
- Gateway 会话中：`/platform resume discord`（无中断）
- 或重启 Gateway：`hermes gateway restart`

注意：Gateway 30s 超时后桥接进程可能仍在重连，不要反复重启 Gateway。多个平台同时失败通常是代理问题。

## Pitfalls

- **安全策略拦截**：读取 Clash 配置文件时优先用 `read_file` 而非终端命令（`cat`/`grep`），后者可能触发 file-mutation-verifier 拦截
- **curl 被安全策略拦截**：如果 `curl --proxy` 被安全策略拒绝，改用 `read_file` 直接读 profiles.yaml 判断
- **时间戳换算**：`extra.expire` 和 `updated` 是 Unix 秒级时间戳，`date -d @<timestamp>` 换算
- **流量单位**：upload/download/total 是字节（Byte），除 1073741824 得 GB
- **多个订阅**：profiles.yaml 可能包含多个 `type: remote` 的订阅，`current` 指定哪个是当前激活的
- **外部控制器**：默认关闭，打开后可通过 `http://127.0.0.1:9097` HTTP API 远程切换节点
- **读取 profiles.yaml**：`read_file` 在文件不存在或路径错误时返回 `file not found`——先确认 profiles.yaml 确实在预期路径下再用

## Prometheus 集成

Clash 的 mihomo 内核暴露 REST API 通过 Unix socket（非 HTTP，因为外部控制器默认禁用）：

```
/tmp/verge/verge-mihomo.sock
```

可用 curl 直接查询：

```bash
# 代理组和节点信息
curl -s --unix-socket /tmp/verge/verge-mihomo.sock http://localhost/proxies

# 版本
curl -s --unix-socket /tmp/verge/verge-mihomo.sock http://localhost/version
```

如果 Hermes Health Exporter 部署了，会自动采集以下 Clash 指标暴露到 Prometheus（端口 9800）：

| 指标 | 说明 |
|------|------|
| `hermes_clash_api` | API 连通性 (0/1) |
| `hermes_clash_total_proxies` | 代理节点总数 |
| `hermes_clash_traffic_remaining_gb` | 剩余流量 GB |
| `hermes_clash_reset_days` | 重置剩余天数 |
| `hermes_clash_main_alive` | 主代理组存活 |
| `hermes_clash_main_node{node="JP-4"}` | 当前选中节点标签 |

这些指标可在 Grafana (http://localhost:3000) 的「Hermes 系统健康看板」的 Clash 机场监控行查看。

## 参考文件

- `references/profiles-example-20260610.md` — 实际诊断记录，包含两个订阅的完整配置、流量、节点选择和恢复检查命令。当 profiles.yaml 格式不清晰时可参考此文件对比解读。
