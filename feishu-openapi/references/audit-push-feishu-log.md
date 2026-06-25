# 安全审计 → 飞书推送操作记录

## 2026-06-23: 首次搭建全链路

### 背景
安全审计脚本 `security-audit.py` 已运行（每日 cron 08:30），但审计报告仅存本地，未推送飞书。

### 搭建步骤
1. 创建 `audit-push-feishu.sh` — 从最新审计报告提取摘要，调用飞书 API 推送
2. 创建 `audit-full-chain.sh` — 封装审计+推送为一步
3. 注册 no-agent cron（`cronjob create`），替代旧的 LLM-based cron
4. 暂停旧 cron（`cronjob pause`）

### 关键坑
- 安全审计脚本退出码为 1 代表"发现异常"（不是错误），full-chain 用 `set -uo pipefail` 而非 `set -euo`
- `.env` 不能 `source`（含特殊字符），逐变量 `grep` 提取
- 审计报告摘要行有一个空行间隔，`grep -A2 ^## 总结 | tail -1`

### 飞书通道已验证参数
- Gateway WebSocket 模式，当前已连接
- Home channel: `ou_a74c0eb0ff0f216d5036c2300a213d22`
- 消息类型: text（富文本需 `msg_type=post`，暂未用）
