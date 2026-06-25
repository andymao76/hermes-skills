# 安全审计 → 飞书推送全链路配置

## 脚本文件

```
~/.hermes/scripts/
├── security-audit.py           # 4模块安全审计扫描
├── audit-push-feishu.sh        # 从最新审计报告提取摘要推飞书
└── audit-full-chain.sh         # 审计+推送一步到位 (no-agent模式)
```

## Cron 配置

```bash
cronjob create \
  --name "安全审计全链路—飞书推送" \
  --schedule "30 8 * * *" \
  --script "audit-full-chain.sh" \
  --no-agent \
  --deliver "local"
```

- no-agent 模式: 0 token 消耗，纯脚本运行
- 每天 08:30 自动执行: 审计扫描 → 报告生成 → 飞书推送
- 审计报告留存: `~/knowledge/_system/security/audit-reports/`
- 报告保留策略: 最近 30 份

## 推送消息格式

```
【每日安全审计报告】2026-06-23
──────────────────
状态: ⚠️ 发现异常
隔离违规: 2 处
敏感词命中: 5 处
──────────────────
⚠️ **发现 1 个隔离问题 + 5 类敏感词命中**
──────────────────
⏰ 10:46:27 | Hermes Security
```

## `.env` 变量提取注意事项

不要在 cron 脚本中使用 `source ~/.hermes/.env`，该文件含特殊字符会导致 shell 崩溃。
使用逐变量 grep 提取：

```bash
FEISHU_APP_ID=$(grep "^FEISHU_APP_ID=" ~/.hermes/.env | head -1 | cut -d= -f2-)
FEISHU_APP_SECRET=*** "^FEISHU_APP_SECRET=*** ~/.hermes/.env | head -1 | cut -d= -f2-)
FEISHU_HOME_CHANNEL=$(grep "^FEISHU_HOME_CHANNEL=" ~/.hermes/.env | head -1 | cut -d= -f2-)
```

## 旧版迁移

旧版 LLM agent 模式的审计 cron 需要暂停或删除，避免每天重复执行:

```bash
cronjob pause <old_job_id>
# 或
cronjob remove <old_job_id>
```
