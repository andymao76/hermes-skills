# Ops 巡检脚本常见误报模式

> 在 Hermes 日常巡检/健康检查脚本中，以下模式**经常产生假告警**，写新脚本或排查异常时应优先排除。

---

## 1. 国内网络环境下 API 直连检测

**症状**: 脚本直接 `curl https://api.deepseek.com` 返回 401，标记为 🔴 网络异常。

**根因**:
- `curl https://api.deepseek.com` 不带 API Key 直接访问，该 endpoint 对所有未认证请求返回 401。
- 在国内环境下，DeepSeek API 需要通过代理才能正常工作（api.deepseek.com 的国内直连路由可能不稳定）。

**正确做法**:
```python
# ❌ 错误：直连测试会误报
direct_test = run("curl -s -o /dev/null -w '%{http_code}' https://api.deepseek.com")

# ✅ 正确：走代理测试，或用带有效 API Key 的真实 chat 调用
proxy_test = run("curl -s -o /dev/null -w '%{http_code}' -x http://127.0.0.1:7897 https://api.deepseek.com/v1/models")
# 或者使用 shemes-doctor-fast（用真实 API Key 发 chat 请求）
```

**适用于**: DeepSeek、SiliconFlow 等国内 provider 的连通性检测。

---

## 2. 使用不可解析的主机名做 ping 检测

**症状**: 脚本标记"腾讯云不可达"，实际只是 `ping tencent` 失败。

**根因**: `/etc/hosts` 中未配置 `tencent` 主机名，DNS 也无法解析，ping 必然失败。

**正确做法**:
```python
# ❌ 错误：依赖主机名解析
ping = run("ping -c 1 -W 2 tencent")

# ✅ 正确：使用真实 IP 或域名
ping = run("ping -c 1 -W 2 123.123.123.123")    # 腾讯云真实 IP
ping = run("ping -c 1 -W 2 tencentcloud.com")    # 或可解析的域名
```

**注意**: 在 `/etc/hosts` 中配别名只适合特定机器，脚本应考虑跨环境可移植性。

---

## 3. 基于日志关键词的 IM 平台状态检测

**症状**: 脚本输出 `tele ? | disc ? | weix ? | what ? | feis ?`，所有平台状态未知。

**根因**: 脚本通过 `grep -i 'connected|error|failed'` 扫描 Gateway 日志，这种检测方式：
- 需要日志恰好包含这些关键词
- 无法区分"已连接"和"连接失败后的重试"
- 受日志滚动/清理影响

**正确做法**:
```python
# ❌ 错误：基于日志关键词匹配
log = run("tail -50 gateway.log | grep -i 'connected|error|failed'")
ok = "✅" if g in log.lower() and 'error' not in log.lower() else "?"

# ✅ 正确：通过 Gateway 内部接口或 systemd 状态查询
# 选项A：检查 systemd 服务中各平台的健康状况
# 选项B：用 hermes cli 查询平台状态
# 选项C：直接尝试发送测试消息（最可靠）
```

---

## 4. Telegram Bot 轮询冲突

**症状**: Gateway 日志反复出现 `Telegram polling conflict` + `resumed after conflict retry` 循环。

**根因**: 同一个 Bot Token 被多个实例轮询（另一个 Hermes Gateway/进程也在运行）。

**检测与修复**:
```bash
# 检查是否有多个 Telegram 轮询进程
ps aux | grep -i telegram | grep -v grep | grep -v telegram-desktop

# 检查是否有另一个 Gateway 进程
ps aux | grep -E "hermes.*gateway" | grep -v grep

# 终止冲突进程
kill -9 <PID>
```

**规则**: 同一时间只能有一个 Gateway 实例轮询同一个 Telegram Bot Token。

---

## 5. 脚本退出码与真实状态不符

**症状**: cron 显示 `last_status: "error"`，但查看脚本输出发现只是级别不高的告警。

**根因**: 脚本使用 `exit FATAL*10 + WARN` 等编码退出码，任何非 0 退出码都被 cron 记为 error。

**判断方法**:
```bash
# 查看 cron 投递的完整输出
cronjob action=list
# 检查 last_delivery_error 和输出内容

# 区分"有警告"和"有故障"
# exit 1:  有警告但功能正常 → 无需处理
# exit 10+: 有致命错误 → 需要人工介入
```

**详见**: `no-agent-exit-codes` skill。

---

## 6. Docker 未运行

**症状**: 脚本标记 `Docker 未运行`。

**根因**: 开发/个人机器上 Docker 不是必须的，没有 Docker 是正常状态。

**建议**: 巡检脚本应区分"Docker 已配置但挂了"和"机器本来就不是 Docker 环境"。可用以下逻辑：

```python
docker_expected = os.path.exists('/var/run/docker.sock') or os.path.isdir('/etc/docker')
if not docker_expected:
    status = "Docker 未安装（预期）"  # 仅记录，不告警
elif not docker_ps:
    status = "❌ Docker 守护进程未运行"  # 这才是真异常
```

---

## 通用原则

| 原则 | 说明 |
|------|------|
| **区分故障与配置** | 脚本检测到的"不可达"未必是故障，可能是配置问题（hostname、代理策略、非必需服务） |
| **中国网络特殊性** | 国内对境外 API 的访问策略（DKN/GFW/路由）可能导致直连失败，但代理下正常 |
| **日志检测不可靠** | 日志只记录了事件，不反映当前状态。grep keywords 容易产生假阳性 |
| **免安装服务** | Docker、某些 IM 平台可能是故意不启用，不应视为异常 |
