# 密钥安全策略

## 规则

API Key、密码、Token **仅存 `/mnt/backup/secrets/`**，永不推送 GitHub。

## 备份位置

```
/mnt/backup/secrets/
├── hermes-config.yaml    ← 完整 config.yaml（含所有 Key）
├── hermes-env.txt        ← .env 环境变量
└── README.md
```

## GitHub 脱敏规则

| 仓库 | 可见性 | 含密钥？ |
|------|:------:|:--------:|
| hermes-config | 🔒 私有 | ❌ 全部替换为 YOUR_API_KEY |
| hermes-worklog-skills | 🔒 私有 | ❌ 纯技能文件 |
| hermes-community-skills | 🌍 公开 | ❌ 纯文本索引 |

## 恢复

```bash
cp /mnt/backup/secrets/hermes-config.yaml ~/.hermes/config.yaml
cp /mnt/backup/secrets/hermes-env.txt ~/.hermes/.env
```

## 保护机制

- `.gitignore` 包含 `.env`, `secrets/`, `config.yaml`
- 超过 20MB 的单文件不推 GitHub
- 知识库（852MB）由 `/mnt/backup/` 保护
- 每日增量备份 03:00 + 每周完整 周日 04:00，保留 60 天
