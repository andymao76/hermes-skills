# Security Audit Protocol

从 Hermes Security Governance Framework v1.0 执行中沉淀的安全审计工作流。

## 触发条件

用户要求执行安全框架/安全检查/安全审计类文档时。

## 标准流程

1. **定位并导入** — 找到目标文件，复制到 `~/knowledge/skills/hermes/security/`
2. **Secret Scanner** — 扫描 `~/.hermes` 和 `~/knowledge` 中的明文 API Key/Token/Password
   ```bash
   grep -RniE "api[_-]?key|secret|token|password" ~/.hermes ~/knowledge
   ```
3. **权限检查** — 验证关键路径权限：
   - `~/.hermes` → 700
   - `~/.hermes/.env` → 600
   - `~/.ssh/` → 700，内部私钥 → 600
   - 修复不符合项
4. **Cron 审计** — `hermes cron list` 检查任务数量和异常
5. **修复问题** — 发现的问题立即修复并记录
6. **生成报告** — 写入 `~/knowledge/_system/security_audit/YYYY-MM-DD.md`

## 风险分级

| 级别 | 描述 |
|------|------|
| 🟢 低 | 权限正确、无泄露、cron 正常 |
| 🟡 中 | 备份文件含历史 API Key、单个权限异常 |
| 🔴 高 | 当前配置明文泄露、远程访问权限开放 |

## 常见发现

- **备份文件含 API Key**：`~/.hermes/config.yaml.bak.*` 中的历史明文 Key 是常见风险点
- **SSH 权限松弛**：`known_hosts.old`（644）、`controlmasters`（775）易被忽略
