# 飞书 Cron 推送配置

## 推送目标格式

cron 推送目标使用 `feishu:<chat_id>` 格式：

```yaml
deliver: "feishu:ou_a74c0eb0ff0f216d5036c2300a213d22"          # 推送到用户
deliver: "feishu:oc_a5a593e6822e69661878ae5c2124be35"          # 推送到群聊
deliver: "telegram,feishu:ou_xxx"                               # 多平台
```

- 用户推送使用 `open_id`（`ou_` 开头）
- 群聊推送使用 `chat_id`（`oc_` 开头）
- `FEISHU_HOME_CHANNEL` 环境变量配置默认目标

## 更新已有 cron 的推送目标

```bash
# 更新推送目标
hermes cron update <job_id> --deliver "telegram,feishu:ou_a74c0eb0ff0f216d5036c2300a213d22"

# 或通过 Hermes Agent 交互操作
cronjob(action='update', job_id='xxx', deliver='telegram,feishu:ou_xxx')
```

## 验证推送是否正常

1. 确认飞书 Gateway WebSocket 已连接：
   ```bash
   journalctl --user -u hermes-gateway.service --no-pager -n 10 | grep "Lark.*connected"
   ```

2. 手动触发 cron 测试：
   ```bash
   hermes cron run <job_id>
   ```
