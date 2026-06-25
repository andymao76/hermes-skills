# 实战案例：备份文件 API Key 泄露

## 事件概况

| 字段 | 值 |
|------|-----|
| 事件类型 | API Key 泄露（P1） |
| 发现方式 | Security Audit SOP 执行 Secret Scanner |
| 涉及文件 | 24 个 config.yaml.bak.* 历史备份 |
| 泄露密钥 | 388 条（sk-xxx 格式） |
| 处置时间 | 约 10 分钟 |

## 时间线

| 时间 | 事件 |
|------|------|
| T+0min | Security Audit 执行 Secret Scanner，发现备份文件中大量明文 API Key |
| T+1min | 确认影响范围：24 个备份文件，覆盖 deepseek/siliconflow/dashscope |
| T+3min | 执行批量替换脚本，388 条 api_key: 值替换为 [REDACTED] |
| T+5min | 验证无残留：grep 确认所有备份文件已脱敏 |
| T+7min | 根本修复：config.yaml api_key 迁移为 api_key_env |
| T+8min | 向 .env 新增 3 个缺失环境变量 |
| T+10min | 二次验证完成 |

## 根因分析 (5 Whys)

1. 为什么备份文件有密钥？ → Hermes 每日备份 cron 直接复制 config.yaml
2. 为什么 config.yaml 有明文？ → 部分 provider 用 api_key 硬编码而非 api_key_env
3. 为什么未被早期发现？ → 未执行系统化 Secret Scanner
4. 为什么备份策略未考虑密钥脱敏？ → SOP 中未定义备份文件密钥清理流程

## 整改措施

| # | 措施 | 状态 |
|---|------|------|
| 1 | config.yaml 全部 api_key → api_key_env | ✅ 已完成 |
| 2 | 新增缺失环境变量到 .env | ✅ 已完成 |
| 3 | 备份文件脱敏脚本纳入 SOP | ✅ 已完成 |
| 4 | 定期 Secret Scanner（每日 cron） | ⏳ 待配置 |

## 技术要点

- 批量替换使用 Python re.sub()，同时处理 `api_key: sk-xxx` 和 `api_key: 'sk-xxx'`
- .env 含 shell 特殊字符，需逐行提取而非 source
- config.yaml 受安全守卫保护，需 sed -i 编辑
- 密钥值在终端输出中截断为 ***，需 Python open() 直接读取字节
