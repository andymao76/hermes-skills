# 全系统综合健康检查报告

当用户要求"全面系统健康检查"时，以下为完整的报告结构模板。覆盖系统基础、硬件、进程、网络、MCP、大模型、IM平台、定时任务 8 个维度。

## 报告生成工作流

### 数据采集（并行执行）

同时发起多项 terminal 调用，不要串行等待：

```bash
# 批次1: 磁盘 + 内存 + 硬件
terminal(command="df -h && free -h && uptime && mount")
# 批次2: 网络 + 代理
terminal(command="curl baidu && curl google(代理) && ss -tlnp")
# 批次3: Hermes + MCP
terminal(command="hermes status && hermes mcp list")
# 批次4: 定时任务
terminal(command="hermes cron list")
# 批次5: 知识库
terminal(command="curl -s http://localhost:6333/collections | python3 -m json.tool || echo 'kb-index: Qdrant 集合检查失败'")
```

### TODO 进度跟踪

```python
todo(merge=true, todos=[
  {"id": "disk", "content": "磁盘检查", "status": "in_progress"},
  {"id": "memory", "content": "内存/CPU", "status": "pending"},
  ...
])
```

## HTML 报告模板

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<style>
:root { --bg: #0d1117; --card: #161b22; --border: #30363d;
        --text: #c9d1d9; --green: #3fb950; --yellow: #d29922; --red: #f85149; }
body { font-family: -apple-system, ...; background: var(--bg); color: var(--text); }
.grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.card { background: var(--card); border: 1px solid var(--border); border-radius: 8px; padding: 16px; }
.stat-row { display: flex; justify-content: space-between; padding: 4px 0; }
.ok { color: var(--green); } .warn { color: var(--yellow); } .err { color: var(--red); }
.badge-ok { background: #1a3d2b; color: var(--green); }
.badge-warn { background: #3d2e1a; color: var(--yellow); }
.badge-err { background: #3d1a1a; color: var(--red); }
</style>
</head>
<body>
<div class="container">

<h1>🩺 系统健康检查报告</h1>
<div class="subtitle">日期 · 主机名 · 备份盘状态</div>

<!-- 总体评估横幅 -->
<div class="card" style="border-left:4px solid var(--green);">
  <span>✅ 系统状态良好 / ⚠️ 有警告 / ❌ 有问题</span>
  <div>正常 N 项 · 警告 N 项 · 已修复 N 项</div>
</div>

<!-- 硬件 -->
<div class="section-title">💻 硬件与系统</div>
<div class="grid">
  <div class="card"><h2>CPU</h2>...</div>
  <div class="card"><h2>内存</h2>...</div>
  <div class="card"><h2>磁盘</h2>...</div>
  <div class="card"><h2>备份盘</h2>...</div>
</div>

<!-- 高资源进程表 -->
<div class="card full">
  <h2>🔥 高资源占用</h2>
  <table><tr><th>PID</th><th>CPU%</th><th>MEM%</th><th>命令</th></tr>...</table>
</div>

<!-- Hermes Agent -->
<div class="section-title">🤖 Hermes Agent</div>
<div class="grid">...</div>

<!-- MCP 服务器表 -->
<div class="section-title">🔌 MCP 服务器</div>
<div class="card full"><table>...</table></div>

<!-- 定时任务表 -->
<div class="section-title">⏰ 定时任务</div>
<div class="card full"><table>...</table></div>

<!-- 架构完整性验证（非常重要） -->
<div class="section-title">🏗️ 架构完整性</div>
<div class="card full">
<table>
<thead><tr><th>路径</th><th>类型</th><th>目标</th><th>状态</th></tr></thead>
<tbody>
<tr><td>~/.npm-global</td><td>symlink</td><td>/mnt/backup/.../npm-global</td><td class="ok">✅</td></tr>
<tr><td>~/.npm</td><td>symlink</td><td>/mnt/backup/.../npm</td><td class="ok">✅</td></tr>
<tr><td>~/Documents</td><td>local dir</td><td>Obsidian Vault</td><td class="ok">✅</td></tr>
<tr><td>~/Pictures</td><td>symlink</td><td>/mnt/backup/.../Pictures</td><td class="ok">✅</td></tr>
<tr><td>~/code</td><td>symlink</td><td>/mnt/backup/.../code</td><td class="ok">✅</td></tr>
<tr><td>~/knowledge/工作</td><td>symlink</td><td>→ Documents/Obsidian Vault/工作</td><td class="ok">✅</td></tr>
</tbody>
</table>
</div>

<!-- 问题与修复 -->
<div class="section-title">🔧 问题与修复</div>
<div class="card full">
<h2>✅ 已修复</h2>
<div class="issue-item">...</div>
</div>
<div class="card full">
<h2>⚠️ 已知问题</h2>
<div class="issue-item">...</div>
</div>

<!-- 监听端口表 -->
<div class="section-title">🔌 监听端口</div>
<div class="card full"><table>...</table></div>

<div class="footer">报告生成时间 · Hermes Agent 版本</div>
</div>
</body>
</html>
```

## 架构验证检查项

| 路径 | 预期类型 | 预期目标 | 验证命令 |
|------|---------|---------|---------|
| ~/.npm-global | symlink | /mnt/backup/home-sync/data/npm-global | `ls -la ~/.npm-global` |
| ~/.npm | symlink | /mnt/backup/home-sync/cache/npm | `ls -la ~/.npm` |
| ~/Documents | local dir | Obsidian Vault | `ls -la ~/Documents` |
| ~/Pictures | symlink | /mnt/backup/home-sync/userdata/Pictures | `readlink ~/Pictures` |
| ~/Downloads | symlink | /mnt/backup/home-sync/data/Downloads | `readlink ~/Downloads` |
| ~/code | symlink | /mnt/backup/home-sync/userdata/code | `readlink ~/code` |
| ~/LI | symlink | /mnt/backup/home-sync/userdata/LI | `readlink ~/LI` |
| ~/knowledge/工作 | symlink | ~/Documents/Obsidian Vault/工作 | `ls -la ~/knowledge/工作` |
| ~/knowledge/0sinovatio | symlink | ~/Documents/Obsidian Vault/0sinovatio | `ls -la ~/knowledge/0sinovatio` |
| ~/knowledge/工作报告 | symlink | ~/Documents/Obsidian Vault/工作报告 | `ls -la ~/knowledge/工作报告` |

## 常见问题处理

### 备份盘未挂载
- 症状：大量断链指向 /mnt/backup/
- 正确处理：告知用户 `sudo mount /dev/sda2 /mnt/backup`
- 错误处理：❌ 重建本地目录

### NPM 包缺失（filesystem / obsidian MCP 断连）
- 症状：hermes mcp list 显示 filesystem/obsidian 为 connecting 而非 enabled
- 正确处理：先检查备份盘挂载状态，挂载后软链接自动恢复
- 如果备份盘正常但 npm-global 真的丢失：`npm install -g @modelcontextprotocol/server-filesystem obsidian-mcp-server`

### Hermes Gateway 停止
- 症状：im 平台无法收发消息
- 修复：`systemctl --user start hermes-gateway`
- 验证：`hermes status` 查看 Gateway 状态

## 检查命令集合

```
# 系统全面健康报告

## 1️⃣ 系统基础
| 项目 | 状态 | 详情 |
|------|:----:|------|
| 主机名 | ✅ | $(hostname) |
| 内核 | ✅ | $(uname -r) |
| 运行时间 | ✅ | $(uptime -p) |
| 系统负载 | ✅ | $(cat /proc/loadavg) |
| 僵尸进程 | ✅/❌ | $(ps aux | awk '$8=="Z"' | wc -l) |

## 2️⃣ 硬件资源
| 项目 | 状态 | 详情 |
|------|:----:|------|
| CPU | ✅ | 型号 / 核数 |
| 内存 | ✅/⚠️ | 总量/已用/百分比 |
| 磁盘 / | ✅/⚠️ | 总量/已用/百分比 |
| 交换分区 | ✅/⚠️ | 总量/已用 |

## 3️⃣ 关键进程
| 进程 | PID | CPU | 内存 | 状态 |
|------|:---:|:---:|:----:|:----:|
| 每行一个关键进程 |

## 4️⃣ 网络与代理
| 项目 | 状态 | 详情 |
|------|:----:|------|
| 代理端口 | ✅/❌ | 7897 |
| 外网连通 | ✅/❌ | Google 204 |
| 监听端口 | ✅ | 各端口列表 |

## 5️⃣ MCP 服务器
8/8 全部在线 / 部分异常

## 6️⃣ 大模型 API
| Provider | 状态 |
|----------|:----:|
| DeepSeek | ✅ |

## 7️⃣ 定时任务
N 个任务，正常/异常

## 8️⃣ 待处理问题
- ⚠️/❌ 问题列表
```

## 检查命令集合

```bash
# 1. 系统基础
uname -a
uptime -p
cat /proc/loadavg
ps aux | awk '$8=="Z"' | wc -l

# 2. 硬件
lscpu | grep -iE "Model name|型号名称" | head -1
free -h | grep -E "Mem|内存|Swap|交换"
df -h / | tail -1
swapon --show

# 3. 进程
ps aux | grep -E "hermes.*gateway|verge-mihomo|clash-verge|bridge\.js|chrome.*headless" | grep -v grep
docker ps --format "table {{.Names}}\t{{.Status}}"
hermes mcp list 2>&1

# 4. 网络
ss -tlnp | grep -E "7897|3000|9222|3001|8443|18060"
curl -s -o /dev/null -w "%{http_code}" --max-time 5 -x http://127.0.0.1:7897 https://www.google.com/generate_204
curl -s --noproxy '*' -o /dev/null -w "%{http_code}" --max-time 5 https://api.deepseek.com

# 5. 大模型
~/bin/hermes-doctor-fast 2>&1 | grep -E "Provider|✓|✗"

# 6. 定时任务
cronjob action=list  | python3 -c "import sys,json; j=json.load(sys.stdin); [print(f\"{x['name']}: {x['last_status']}\") for x in j.get('jobs',[]) if x.get('last_status') not in ('ok',None)]"
```
