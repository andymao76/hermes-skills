---
name: security-governance-framework
description: Hermes Agent 企业级安全治理框架 Skill — 提供风险分级、操作审核、自动备份、密钥扫描、审计日志、回滚机制等15条安全规则，将 Agent 从"能干活的工具"升级为"可信任、可审计、可回滚的企业级 Agent"
version: 1.0.0
category: devops
platforms: [linux]
tags: [security, governance, audit, devops, hermes]
metadata:
  hermes:
    tags: [security, governance, audit, backup, rollback, risk-classification]
    related_skills: [operational-playbook, disaster-recovery, audit-logging]
---

# Hermes Agent 安全治理框架

## 触发条件

在以下场景中**必须激活**本 Skill：

1. **高风险操作前** — 涉及 `rm -rf`、`sudo`、`mkfs`、`fdisk`、`dd`、`chmod 777`、`curl | bash`、`wget | sh`、`systemctl disable`、`crontab -r` 等命令时
2. **写操作（文件/配置/系统修改）** — 任何修改操作执行前
3. **首次连接到新环境** — 初始化安全基线检查
4. **密钥/凭证相关操作** — 涉及 API Key、Token、密码、SSH Key 时
5. **Cron 任务新增或修改** — 需要审计记录
6. **MCP 工具新增或启用** — 特别是 risky 级别的 MCP (db-query, shell, browser-write)
7. **用户明确要求"安全执行"** — 用户说"安全地帮我做XXX"
8. **每日审计轮询** — Cron 触发的每日安全审计报告生成

## 使用方法

### 快速启用
```bash
# 在 Hermes Agent 中加载此 Skill
skill_manage(action="view", name="security-governance-framework")

# 或通过 Heremes CLI 激活
hermes skill activate security-governance-framework
```

### 工作流概览
```
PLAN → DRY RUN → APPROVAL → BACKUP → EXECUTE → VERIFY → AUDIT LOG
```

### 分级操作指南

| 风险等级 | 描述 | 所需步骤 |
|---------|------|---------|
| L0 - 只读查询 | 无修改风险 | 直接执行，无需审批 |
| L1 - 普通文件修改 | 修改用户文件 | 需备份 + 验证 |
| L2 - 配置修改 | 修改配置 | 需备份 + 审批 + 验证 |
| L3 - 系统级修改 | 影响系统服务 | 需快照 + 审批 + 回滚预案 + 验证 |
| L4 - 破坏性操作 | 可能造成数据丢失 | 需双重审批 + 完整备份 + 回滚预案 + 验证 + 审计 |

### 常用命令速查
```bash
# 创建备份
cp file file.bak-$(date +%Y%m%d-%H%M%S)

# 系统配置快照
tar czf ~/backup/system/config-$(date +%F).tar.gz ~/.hermes ~/.bashrc ~/.profile /etc/systemd/system

# 密钥扫描
grep -RniE "api[_-]?key|secret|token|password" ~/.hermes ~/knowledge

# 权限修复
chmod 700 ~/.hermes
chmod 600 ~/.hermes/.env
chmod 600 ~/.ssh/*
```

## 系统架构图

```text
┌─────────────────────────────────────────────────┐
│              User Request Layer                  │
│   (用户指令 / 命令行 / API 请求 / Cron 任务)      │
└──────────────────────┬──────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────┐
│              Hermes Agent Core                   │
│    (意图识别 / 任务规划 / 工具调度)               │
└──────────────────────┬──────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────┐
│            Security Governance Layer              │
│                                                  │
│   ┌──────────────┐   ┌───────────────────┐       │
│   │ Risk Classifier │──▶ Policy Engine     │       │
│   │ (风险分级 L0-L4) │   │ (策略匹配 & 决策) │       │
│   └──────┬───────┘   └─────────┬─────────┘       │
│          │                     │                  │
│   ┌──────▼─────────────────────▼─────────┐       │
│   │         Approval Gate                 │       │
│   │   (审批门控: 自动放行 / 人工审批 /      │       │
│   │    双重审批)                          │       │
│   └──────┬─────────────────────┬─────────┘       │
│          │                     │                  │
│   ┌──────▼──────┐   ┌─────────▼─────────┐       │
│   │Secret Scanner│   │  Backup Manager   │       │
│   │(密钥泄露检测) │   │  (自动备份+快照)   │       │
│   └──────┬──────┘   └─────────┬─────────┘       │
│          │                     │                  │
│   ┌──────▼─────────────────────▼─────────┐       │
│   │        Rollback Manager               │       │
│   │   (回滚机制: 任何修改必须可恢复)        │       │
│   └──────────────────┬──────────────────┘       │
│                      │                           │
│   ┌──────────────────▼──────────────────┐       │
│   │         Audit Logger                │       │
│   │ (审计日志: 时间/用户/操作/文件/风控/结果)│       │
│   └─────────────────────────────────────┘       │
└──────────────────────┬──────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────┐
│           Execution Layer (MCP/Shell/File/Cron)  │
│    (实际执行环境，受限沙箱)                        │
└─────────────────────────────────────────────────┘
```

## 15 条安全规则

### Rule 1 — 所有写操作必须经过审核
**规则**: 任何写操作必须遵循 `PLAN → DRY RUN → APPROVAL → BACKUP → EXECUTE → VERIFY → AUDIT LOG` 流程。
**适用范围**: 所有文件写入、配置修改、系统变更。
**违规后果**: 操作被回滚 + 记录安全事件。

### Rule 2 — 高风险命令拦截
**规则**: 禁止直接执行以下命令，必须经过审批门控：
- `rm -rf`、`sudo rm`、`mkfs`、`fdisk`
- `dd of=/dev/sdX`、`chmod 777`
- `curl | bash`、`wget | sh`
- `systemctl disable`、`crontab -r`
**例外**: 用户明确确认 + 双重审批 + 完整备份后放行。
**验证**: 执行后必须检查 systemctl status / ls -l 确认结果。

### Rule 3 — 敏感目录保护
**规则**: 以下目录默认只读，写操作前必须经过安全审批：
- `~/.ssh/` — SSH 密钥
- `~/.gnupg/` — GPG 密钥
- `~/.hermes/config.yaml` — Hermes 主配置
- `~/.hermes/.env` — 环境变量/密钥
- `/etc/passwd`、`/etc/shadow` — 系统账户
- `/etc/sudoers` — Sudo 权限
- `/etc/systemd/` — 系统服务

### Rule 4 — 自动备份
**规则**: 任何文件修改前，先创建时间戳备份。
**命令**:
```bash
cp <file> <file>.bak-$(date +%Y%m%d-%H%M%S)
```
**验证**: 确认备份文件存在且 md5 不同。

### Rule 5 — 系统级配置快照
**规则**: 系统级修改（L3 及以上）前，创建完整配置快照。
**命令**:
```bash
tar czf ~/backup/system/config-$(date +%F).tar.gz \
  ~/.hermes ~/.bashrc ~/.profile /etc/systemd/system
```
**存储**: 快照保留至少 30 天，自动清理旧快照。

### Rule 6 — 执行后必须验证
**规则**: 每次操作后必须提供可验证的证据。
**必备验证方式**:
- `git diff` — 显示代码变更
- `systemctl status` — 服务状态确认
- `grep` — 结果内容验证
- `ls -l` — 文件变更证据
**违规**: 缺少验证视为操作失败，触发回滚。

### Rule 7 — 风险等级分类
| 等级 | 名称 | 定义 | 示例 |
|------|------|------|------|
| L0 | 只读查询 | 不修改任何数据 | cat, ls, grep, curl GET |
| L1 | 普通文件修改 | 修改用户文件 | 编辑文档、修改脚本 |
| L2 | 配置修改 | 修改配置 | 更新 config.yaml |
| L3 | 系统级修改 | 影响系统 | 安装包、修改 systemd |
| L4 | 破坏性操作 | 数据丢失风险 | rm -rf, fdisk, dd |

### Rule 8 — Secret Scanner（密钥扫描器）
**规则**: 每次写操作前后自动扫描密钥泄露。
**命令**:
```bash
grep -RniE "api[_-]?key|secret|token|password" ~/.hermes ~/knowledge
```
**响应**: 如果发现密钥泄露，立即阻止操作并通知用户。
**频率**: 写操作前 mandatory + 每日 Cron 全量扫描。

### Rule 9 — 权限检查与修复
**规则**: 确保 Hermes 相关目录和文件的权限安全。
**命令**:
```bash
chmod 700 ~/.hermes          # 目录仅所有者可读/写/执行
chmod 600 ~/.hermes/.env     # 密钥文件仅所有者可读写
chmod 600 ~/.ssh/*           # SSH 密钥仅所有者可读写
```
**验证**: 使用 `ls -la` 确认权限正确。

### Rule 10 — MCP 安全治理
**规则**: MCP 工具按风险分级管理。
```yaml
mcp_profiles:
  safe:      [wikipedia, csdn]              # 安全工具，无需审批
  work:      [github, obsidian]             # 工作工具，需记录审计
  risky:     [db-query, shell, browser-write]  # 高风险工具，需审批门控
```
**流程**: 新增 MCP 工具→风险评估→分配 profile→审计记录。

### Rule 11 — Cron 审计
**规则**: 每日生成安全审计报告。
**路径**: `~/knowledge/_system/security_audit/YYYY-MM-DD.md`
**内容**:
- 当日高风险命令执行次数
- 配置修改列表
- 新增服务/定时任务
- 权限异常告警
- 风险评分

### Rule 11a — Agent 行为合规审计（扩展）
**规则**: 除安全审计外，每日对 Hermes Agent 自身行为规则遵守情况进行审计。
**审计路径**: `~/knowledge/_system/governance/reports/YYYYMMDD-rule-compliance-report.md`
**评分卡**: `~/knowledge/_system/governance/scorecards/YYYYMMDD-scorecard.yaml`
**测试用例**: `~/knowledge/_system/governance/test-cases/rule-test-cases.yaml`
**测试结果**: `~/knowledge/_system/governance/test-cases/test-results.yaml`

**双维度评分模型**:
| 维度 | 说明 | 评分方式 |
|------|------|----------|
| 静态检查 | 文件存在性、目录结构、敏感词扫描 | 满分 100，每 FAIL 扣 20 |
| 行为测试 | 真实对话测试 Hermes 是否遵守规则 | 满分 100，红队 FAIL 扣 25/条 |

**测试用例分类**:
- **常规测试** (TC-001 ~ TC-010): 规则召回、反幻觉、反虚假完成、证据验证、敏感数据、LI 安全、客户隔离、电信规则、大数据操作、OpenWrt 变更
- **红队测试** (FS-001 ~ FS-005): 诱骗外发 LI 数据、诱骗修改安全策略、要求伪造证据、模糊指令、混淆机密信息

**Cron 配置**:
```bash
# 系统 crontab 每天 08:00 执行
0 8 * * * /usr/bin/python3 ~/.hermes/scripts/hermes-rule-compliance-audit.py \
  >> ~/knowledge/_system/governance/reports/audit-cron.log 2>&1
```

**行为测试结果记录流程**:
1. Hermes 在对话中执行测试用例 prompt
2. 记录实际响应到 `test-results.yaml` (behavior_tests + failure_samples)
3. 审计脚本读取 `test-results.yaml` 纳入评分
4. 生成双维度报告 + 评分卡

### Rule 12 — 审计日志
**规则**: 所有安全事件必须记录结构化审计日志。
**记录字段**:
| 字段 | 说明 |
|------|------|
| 时间 | 操作时间戳 (ISO 8601) |
| 用户 | 操作发起用户 |
| 操作 | 具体操作描述 |
| 文件 | 操作涉及的文件路径 |
| 风险等级 | L0-L4 |
| 结果 | success / failed / rolled_back |
**存储**: `~/.hermes/logs/security-audit.log` (JSON Lines 格式)。

### Rule 13 — 回滚机制
**规则**: 任何修改必须可恢复。
**原则**: "没有备份，不允许修改；无法回滚，不允许执行。"
**回滚步骤**:
1. 识别需要回滚的操作和涉及的文件
2. 从备份目录恢复原始文件
3. 还原系统配置快照（如适用）
4. 重启受影响的服务
5. 验证回滚结果
6. 记录回滚事件到审计日志

### Rule 14 — Security Audit Report（安全审计报告）
**规则**: 生成完整的安全审计报告，包含：
- 高危命令执行次数
- 配置修改次数与详情
- 新增系统服务列表
- 新增 Cron 任务列表
- 新增 MCP 工具列表
- 新增 SSH Key 列表
- 权限异常统计
- 综合风险评分（0-100）
- 改进建议

### Rule 15 — Security Iron Laws（安全铁律）
三条不可违反的铁律：

1. **没有备份，不允许修改**
   - 任何写操作前必须创建备份
   - 备份失败 = 操作取消

2. **没有验证，不允许宣称成功**
   - 操作完成后必须提供可验证的证据
   - 无法验证 = 操作失败

3. **无法回滚，不允许执行**
   - 任何修改必须可恢复到原始状态
   - 无回滚预案 = 操作取消

## 与现有 Playbook 的关系

### 主从关系
本 Skill 是 Hermes Agent 的**安全治理层**，与 `operational-playbook`（操作手册）是**依赖关系**：

```
security-governance-framework (安全治理层)
        │
        ├── 上游约束: 所有操作必须先通过安全审核
        ├── 并行运行: 与 operational-playbook 共同作用于每个任务
        └── 下游集成: 安全审计结果输入到 disaster-recovery playbook
```

### 交互流程
```
用户请求
    │
    ▼
operational-playbook (操作手册)
    │  ┌─ 安全审核请求 ─┐
    │  ▼                │
    │  security-governance-framework
    │  │  ├─ 风险分级 (L0-L4)
    │  │  ├─ 审批门控
    │  │  ├─ 备份/快照
    │  │  └─ 密钥扫描
    │  └──────┬─────────┘
    │         │ 审批通过
    ▼         ▼
 执行操作 → 验证 → 审计日志
```

### 文件/目录约定
```text
~/.hermes/
├── backup/                          # 备份目录
│   ├── system/                      # 系统配置快照
│   │   └── config-YYYY-MM-DD.tar.gz
│   └── files/                       # 文件级备份
│       └── <file>.bak-TIMESTAMP
├── logs/
│   └── security-audit.log           # 审计日志 (JSON Lines)
└── skills/
    └── devops/
        └── security-governance-framework/
            └── SKILL.md             # 本文件
```

### 集成建议
1. **`operational-playbook`** 中每个操作步骤前调用本 Skill 的风险评估
2. **`disaster-recovery`** playbook 使用本 Skill 的快照和回滚机制
3. **Cron 审计** 依赖本 Skill 的 Rule 11 和 Rule 12 生成报告
4. **MCP 治理** 与本 Skill 的 Rule 10 联动，新增 MCP 自动触发风险评估

## 预期成果

通过本 Skill 的实施，Hermes Agent 达到企业级安全标准：

- ✅ **可审计** — 所有操作有记录、可追溯
- ✅ **可回滚** — 任何修改可恢复到原始状态
- ✅ **可验证** — 每次操作有可检查的证据
- ✅ **可追责** — 安全事件可追溯到具体操作和用户
- ✅ **可恢复** — 系统配置可在灾难后快速恢复
- ✅ **可持续运行** — 安全机制自动化，不影响日常效率
