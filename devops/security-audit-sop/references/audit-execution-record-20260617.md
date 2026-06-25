# 安全审计实战报告 — 2026-06-17

## 审计范围

首次执行完整安全审计，基于 Security Governance Framework v1.0 的 15 条规则。

## 检查结果

### 1. Secret Scanner

| 扫描范围 | 发现 | 处理 |
|----------|------|------|
| config.yaml 活跃配置 | ✅ 无明文密钥残留（迁移后） | 已执行 api_key→api_key_env 迁移 |
| config.yaml.bak.* (24 个) | ⚠️ 388 条明文 API Key | ✅ 全部替换为 [REDACTED] |
| ~/knowledge/ | ✅ 无敏感信息泄露 | — |

### 2. 权限检查

| 路径 | 权限 | 初始状态 | 处理 |
|------|------|----------|------|
| ~/.hermes | 700 | ✅ 正确 | — |
| ~/.hermes/.env | 600 | ✅ 正确 | — |
| ~/.ssh | 700 | ✅ 正确 | — |
| ~/.ssh/known_hosts.old | 644 → **600** | ❌ 过松 | ✅ 已修复 |
| ~/.ssh/controlmasters | 775 → **700** | ❌ 过松 | ✅ 已修复 |

### 3. Cron 审计

- 活跃 Cron 任务: 20 个
- 失败任务: 2 个（微信推送 rate limit — 非安全问题）
- 备份相关: ✅ 每日备份 + 每周完整备份
- 安全审计: ✅ 已有 Hermes Knowledge Security Audit cron

### 4. 综合风险评分

| 类别 | 评分 | 说明 |
|------|------|------|
| 权限控制 | 🟢 低 | 关键路径权限已修正 |
| 密钥管理 | 🟢 低 | 备份已脱敏，config 已迁移到 api_key_env |
| Cron 安全 | 🟢 低 | 无可疑 Cron |
| **综合** | **🟢 低风险** | |

## 已执行修复

- ✅ ~/.ssh/known_hosts.old → 600
- ✅ ~/.ssh/controlmasters → 700
- ✅ 24 个备份文件 → 388 条密钥 → [REDACTED]
- ✅ config.yaml → 4 个 provider api_key→api_key_env 迁移
- ✅ .env → 新增 SILICONFLOW_API_KEY / SILICONFLOW_CN_API_KEY
- ✅ 审计日志目录结构已创建
- ✅ 框架文件已导入知识库
- ✅ Enzyme 语义索引已重建

## 生成的审计报告

```
~/knowledge/_system/security_audit/2026-06-17.md
```

## 建议后续操作

1. 配置每日安全审计 cron: `hermes cron create "0 8 * * *" --name "security-audit" --script ...`
2. 将 `~/.hermes/config.yaml.bak.*` 的清理纳入每日健康检查
3. 在 config.yaml 中启用 `approvals.mode: manual` 为写操作增加审批门
