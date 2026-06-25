# Inbox 自动归档管线

## 架构

```
消息来源（Feishu/WeChat/WhatsApp/Telegram）
    ↓  Agent 识别关键词自动触发
feishu_to_inbox.py  ←  ~/.hermes/scripts/feishu_to_inbox.py
    ↓
~/knowledge/inbox/{feishu,whatsapp,quick_notes}/
    ↓  cron 每日 22:30
inbox_sorter.py  ←  ~/.hermes/scripts/inbox_sorter.py
    ↓
~/knowledge/{worklog/daily,projects,sksills/troubleshooting,...}/
```

## 触发关键词

当用户消息开头为以下关键词时，Agent 自动将其保存到 inbox：

| 关键词 | 保存位置 | 最终归档目标 |
|--------|----------|-------------|
| `记录：` | inbox/feishu/ | worklog/daily/ |
| `项目：` | inbox/feishu/ | projects/项目名/ |
| `故障：` | inbox/feishu/ | skills/troubleshooting/ |
| `经验：` | inbox/feishu/ | skills/troubleshooting/ |
| `知识：` | inbox/feishu/ | 留在 inbox |

## feishu_to_inbox.py

位置: `~/.hermes/scripts/feishu_to_inbox.py`

```python
from feishu_to_inbox import save_message
path = save_message(text, source='feishu', sender='unknown')
# 返回保存的文件路径
```

CLI 模式:
```bash
python3 ~/.hermes/scripts/feishu_to_inbox.py 记录：今天完成了XX任务
echo '项目：A1项目跟进' | python3 ~/.hermes/scripts/feishu_to_inbox.py
```

文件命名: `YYYYMMDD_HHMMSS_{分类}_{摘要}.md`

## inbox_sorter.py

位置: `~/.hermes/scripts/inbox_sorter.py`

自动分类规则（正则匹配第一行）：

| 规则 | 匹配内容 | 目标目录 |
|------|---------|---------|
| 项目 | `^项目[：:]` 或 `A1\|NISS` 等 | projects/ |
| 排错 | `^故障[：:]` 或 `^经验[：:]` 或 `失败\|异常\|断开` | skills/troubleshooting/ |
| 大数据 | `Kafka\|Flink\|HDFS\|HBase` 等 | skills/bigdata/ |
| 电信 | `ETSI\|3GPP\|HI2\|Wireshark` 等 | skills/telecom/ |
| 记录/默认 | `^记录[：:]` 或无匹配 | worklog/daily/ |

默认兜底: 匹配不到任何规则 → worklog/daily/

## cron 配置

```bash
hermes cron create "22:30" \
  --name "inbox-auto-sort" \
  --prompt "执行 inbox 自动分类归档: python3 ~/.hermes/scripts/inbox_sorter.py" \
  --deliver "origin"
```
