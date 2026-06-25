# P3 OpsAgent + P6 第二大脑同步 — 实现参考

## P3：运维Agent

### ops_agent.py
`~/.hermes/scripts/ops_agent.py`

每日自动巡检脚本，覆盖以下8大维度：
1. **系统基础** — 运行时间、负载、内存、磁盘、温度、僵尸进程
2. **硬件** — CPU/GPU/内存/磁盘/温度
3. **网络** — 代理端口(7897)、外网连通(Google 204)、API 直连(DeepSeek/SiliconFlow)
4. **Gateway** — systemd 运行状态、启动时间
5. **Docker** — 容器列表及状态
6. **MCP** — 进程数量
7. **IM平台** — Telegram/Discord/Feishu/WeChat/WhatsApp/QQ 连接状态
8. **腾讯云** — 远程 SSH 可达性

输出结构化报告到 `~/knowledge/worklog/daily_health/YYYY-MM-DD.md`
异常时推送到当前通道。

### cron 配置
```yaml
每日 09:00 → ops_agent.py → worklog/daily_health/ + 异常告警
```

## P6：第二大脑同步

### feishu_to_inbox.py
`~/.hermes/scripts/feishu_to_inbox.py`

从 Feishu/WeChat/Telegram 消息 → knowledge inbox。

**三种调用方式：**
```bash
# 参数模式
python3 feishu_to_inbox.py 记录：内容

# 管道模式
echo "内容" | python3 feishu_to_inbox.py

# API 模式（供 webhook 调用）
from feishu_to_inbox import save_message
save_message("记录：内容", source="feishu", sender="user_id")
```

**自动检测前缀：**
| 前缀 | 文件名 | 最终归档 |
|------|--------|---------|
| `项目：` | `proj_*` | `projects/项目名/` |
| `记录：` | `note_*` | `worklog/daily/` |
| `故障：` | `trouble_*` | `skills/troubleshooting/` |
| `经验：` | `exp_*` | `skills/（按内容）` |
| `知识：` | `k_*` | 留在 inbox |

### inbox_sorter.py
`~/.hermes/scripts/inbox_sorter.py`（增强版，支持 os.walk 递归扫描子目录）

**分类规则：**
```python
规则按优先级顺序匹配首行关键词：
  项目/NISS/A1 → projects/a1_pc_project/
  签证/visa → projects/us_visa/
  Apple Notes/iCloud → projects/apple_notes_sync/
  故障/经验/报错/error/failed/异常 → skills/troubleshooting/
  Kafka/Flink/HDFS/HBase/YARN/Greenplum → skills/bigdata/
  ETSI/3GPP/HI2/ASN.1/SIP/Wireshark → skills/telecom/
  巡检/维护 → worklog/daily/
  记录 → worklog/daily/
  默认 → worklog/daily/
```

### cron 配置
```yaml
每日 22:30 → inbox_sorter.py → 自动分类归档
```

## 行为规则（Agent 侧）

当用户在任意平台（Feishu/WeChat/Telegram）发送消息，如果首行以以下关键词开头，Agent 自动调用 `feishu_to_inbox.py` 保存：
- `记录：` — 保存到 inbox，当晚自动归档到 worklog/daily/
- `项目：` — 保存到 inbox，当晚自动归档到 projects/
- `故障：` — 保存到 inbox，当晚自动归档到 skills/troubleshooting/
- `经验：` — 保存到 inbox，当晚自动归档到 skills/
- `知识：` — 保存到 inbox，留在收件箱
