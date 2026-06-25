# Ops Agent 每日巡检

## 检查维度

| 维度 | 检查项 | 异常阈值 |
|------|--------|---------|
| 🏠 系统 | CPU 负载、内存使用率、磁盘使用率、运行时间 | 负载>5.0 / 内存>85% / 磁盘>90% |
| 🌐 网络 | Clash 内核状态、代理端口(7897)、Google/DeepSeek/SiliconFlow连通性 | 端口未监听 / 连通 >3s |
| 🚪 Gateway | systemd 状态、运行时长、日志错误数 | 非 active / 最近有 ERROR |
| 🐳 Docker | Open WebUI 容器健康状态 | 非 running/healthy |
| 🔌 MCP | MCP 服务器进程数 | 进程数 < 配置数 |
| 📡 IM | Telegram/Discord/微信/WhatsApp/飞书 各平台状态 | 平台报错 |
| ☁️ 腾讯云 | SSH 可达性 | 连接超时 / 拒绝 |

## ops_agent.py

位置: `~/.hermes/scripts/ops_agent.py`

执行方式:
```bash
python3 ~/.hermes/scripts/ops_agent.py
```

输出: 结构化 markdown 报告，直接打印到 stdout

报告格式:

```markdown
## 运维日报 YYYY-MM-DD HH:MM

### 异常摘要
- ❌ http://xxx (xx service)

### 🏠 系统
| 项目 | 状态 | 详情 |
|------|------|------|

### 🌐 网络
...
```

## cron 配置

```bash
hermes cron create "0 9 * * *" \
  --name "daily-ops-check" \
  --script "ops_agent.py" \
  --no_agent true \
  --workdir "$HOME"
```

`no_agent: true` 模式直接交付脚本 stdout，零 token 开销。

## 扩展

如需增加巡检维度：
1. 在 `checks/` 字典中添加新函数
2. 在 `check_groups` 中添加新分类
3. 输出自动写入 `worklog/daily_health/YYYY-MM-DD.md`
