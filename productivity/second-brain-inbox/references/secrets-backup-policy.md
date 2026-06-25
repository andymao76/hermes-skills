# 密钥与敏感信息备份策略

> 适用: Hermes 配置中的 API Key、Token、密码、密钥文件
> 策略定于 2026-06-11，用户明确指令：**API Key 只存本地，不推 GitHub**

## 铁律

```
API Key / 密码 / Token / secret → 仅 /mnt/backup/secrets/
                                  → 永不推送 GitHub
```

## 存储位置

| 内容 | 路径 | 备份方式 |
|------|------|---------|
| 完整 config.yaml | `/mnt/backup/secrets/hermes-config.yaml` | 本地文件 |
| .env 环境变量 | `/mnt/backup/secrets/hermes-env.txt` | 本地文件 |
| config.yaml.example（脱敏） | GitHub: hermes-config | Key → `YOUR_API_KEY` |

## 恢复命令

```bash
cp /mnt/backup/secrets/hermes-config.yaml ~/.hermes/config.yaml
cp /mnt/backup/secrets/hermes-env.txt ~/.hermes/.env
```

## Git 提交前检查

```bash
grep -n "api_key:" config.yaml.example | grep -v "YOUR_API_KEY\|''"
# 如果输出不为空 → 有真实 Key 泄漏 → 先脱敏再推
```

## GitHub 仓库密钥安全状态

| 仓库 | 含真实 Key? | 措施 |
|------|:----------:|------|
| hermes-config | ❌ 脱敏 | `.gitignore` 排除 `.env`、`secrets/` |
| hermes-worklog-skills | ✅ 纯技能 | 无敏感数据 |
| hermes-community-skills | ✅ 纯文本 | 无敏感数据 |
