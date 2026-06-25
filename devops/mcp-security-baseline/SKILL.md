---
name: mcp-security-baseline
description: MCP 服务器安全基线 — 风险分级、安全检查清单、API Key 管理、调用审计、服务发现管控、禁止运行类型
category: devops
priority: high
tags: [mcp, security, baseline, audit, api-key, risk-assessment, devops]
---

# MCP 服务器安全基线

> 适用环境：Hermes Agent 及所有 MCP 协议服务器  
> 最后更新：2026-06-17

---

## 目录

| # | 章节 | 说明 |
|---|------|------|
| 1 | [MCP 风险分级](#1-mcp-风险分级) | safe / work / risky 三级分类 |
| 2 | [配置安全检查清单](#2-mcp-配置安全检查清单) | 新接入 MCP 必检项 |
| 3 | [API Key 管理](#3-mcp-api-key-管理) | 密钥存储、轮换、泄露处置 |
| 4 | [调用审计](#4-mcp-调用审计) | 调用记录、异常检测、链路追踪 |
| 5 | [服务发现管控](#5-mcp-服务发现管控) | 服务注册、白名单、来源验证 |
| 6 | [禁止运行的 MCP 类型](#6-禁止运行的-mcp-类型) | 明确列入黑名单的 MCP 类别 |

---

## 1. MCP 风险分级

所有 MCP 服务器按功能特权和数据访问范围分为三级：

### 🟢 **safe** — 安全级

| 特征 | 示例 |
|------|------|
| 只读操作，无数据外发 | `mcp-server-time`（获取时间） |
| 对本地文件系统仅有**受限读取**，无写入权限 | `mcp-server-filesystem`（仅限指定目录） |
| 调用公共 API，无认证凭据传递 | Wikipedia MCP、天气查询 |
| 开源、维护活跃、社区认可 | `obsidian-mcp-server` |

**策略**：默认允许。仅需基础配置审查。

### 🟡 **work** — 工作级

| 特征 | 示例 |
|------|------|
| 需要 API Key 或 Token 才能工作 | Github MCP、Linear MCP |
| 对本地文件系统有写入权限 | 文件系统 MCP（写模式） |
| 通过 HTTP/HTTPS 与外部服务通信 | 数据库查询 MCP（配置了外网端点） |
| 执行命令或启动进程 | 容器管理 MCP、部署工具 MCP |

**策略**：需审批接入。必须通过安全检查清单（见 §2）。API Key 必须托管在凭据池（credential pool）中。

### 🔴 **risky** — 风险级

| 特征 | 示例 |
|------|------|
| 可执行任意 Shell 命令 | 执行系统命令的 MCP |
| 可访问敏感数据（密码、密钥、数据库原始内容） | 未沙箱化的数据库 MCP |
| 可读写网络请求（代理、转发） | 代理/隧道类 MCP |
| 来源不明、未审计、闭源 | 第三方未知来源的 MCP |
| 需要 SUDO 权限或 root 级文件访问 | 系统运维类 MCP（未沙箱） |
| 连接未知或未加密的远程端点 | |

**策略**：默认禁止。必须经过安全评审 + 沙箱化 + 限权后才能临时启用。

### 本环境 MCP 风险分级映射

基于 `~/.hermes/config.yaml` 中的 MCP 配置：

| MCP 服务器 | 风险等级 | 理由 |
|------------|---------|------|
| time | 🟢 safe | 只读标准库，无网络 |
| wikipedia | 🟢 safe | 只读公共 API，有代理但可控 |
| obsidian | 🟡 work | 需 API Key，可读写本地笔记 |
| filesystem | 🟡 work | 可读写指定目录 |
| chart | 🟢 safe | 纯数据可视化，无网络 |
| github-gov1 | 🟡 work | 需 API Key（通过 wrapper 脚本） |
| csdn | 🟡 work | 外部服务调用 |
| db-query | 🟡 work | 本地数据库查询，有网络端点 |
| zhihu | 🟡 work | 外部 API 调用 |
| xiaohongshu | 🟡 work | 外部 API 调用 |
| jd | 🔴 risky | 电商平台 MCP，需登录凭据 |
| taobao | 🔴 risky | 电商平台 MCP，需登录凭据 + 浏览器环境 |
| linear | 🟡 work | 通过 OAuth 认证（当前 disabled） |

---

## 2. MCP 配置安全检查清单

新增任何 MCP 服务器前，逐项检查以下内容：

### 🔲 基础检查

| # | 检查项 | 通过标准 | 参考 |
|---|--------|---------|------|
| 1 | 来源可信 | 官方仓库 / 知名开发者 / 已验证签名 | 检查 GitHub Stars、最后更新时间 |
| 2 | 代码审计 | 已阅读核心源码，无可疑行为 | 检查 `command`、`args` 中的脚本内容 |
| 3 | 最小权限 | 只申请完成任务所需的最少权限 | 如只读文件就不给写入权限 |
| 4 | 网络隔离 | 明确知晓 MCP 连接的目标端点 | 检查 `url` 字段和 `env` 中的代理配置 |
| 5 | 配置审核 | `config.yaml` 中无明文敏感信息 | 检查 `env` 段落的密钥 |

### 🔲 网络检查

| # | 检查项 | 通过标准 |
|---|--------|---------|
| 6 | 传输加密 | SSH/TLS 连接，禁止明文 HTTP（除非 localhost） |
| 7 | 端点白名单 | 只连接已知、允许的域名/IP |
| 8 | 出站控制 | 通过代理/防火墙限制不经意的数据外泄 |

### 🔲 运行时检查

| # | 检查项 | 通过标准 |
|---|--------|---------|
| 9 | 超时配置 | 已设置 `connect_timeout` 和 `timeout` |
| 10 | 重连策略 | 连接失败时有合理退避，不无限重试 |
| 11 | 并行调用 | 检查 `supports_parallel_tool_calls` 是否合理 |
| 12 | 资源限制 | 内存/CPU 使用有上限约束 |

### 🔲 数据安全检查

| # | 检查项 | 通过标准 |
|---|--------|---------|
| 13 | 输入净化 | 不对用户输入做 eval/exec |
| 14 | 输出限制 | 返回数据大小有上限 |
| 15 | 日志脱敏 | 不记录 API Key、Token、密码到日志 |
| 16 | 临时数据清理 | 运行结束后清理临时文件和缓存 |

---

## 3. MCP API Key 管理

### 3.1 密钥存储原则

| 原则 | 说明 |
|------|------|
| ❌ 禁止明文存储 | 不在 `config.yaml`、`.env`、代码中硬编码 API Key |
| ❌ 禁止提交到 Git | `.gitignore` 中忽略所有含密钥的文件 |
| ✅ 使用环境变量 | 通过 `env` 字段引用环境变量，如 `$GITHUB_TOKEN` |
| ✅ 使用凭据池 | 配置 `credential_pool_strategies` 统一管理 |

### 3.2 密钥轮换策略

| 密钥类型 | 建议轮换周期 | 触发轮换条件 |
|---------|-------------|-------------|
| 个人 API Token | 90 天 | 离职/权限变更时立即轮换 |
| OAuth 应用密钥 | 按平台策略（通常 1 年） | 泄露怀疑时立刻撤销 |
| 服务账号密钥 | 180 天 | 权限审计后 |

### 3.3 泄露应急处置流程

```
1. 立即禁用泄露密钥
   └→ 撤销 API Key / 吊销 OAuth Token / 旋转 Secret
2. 审计泄露影响范围
   └→ 检查调用日志，确认是否有未授权访问
3. 检查 MCP 日志脱敏是否生效
   └→ grep 确认密钥未出现在日志文件中
4. 生成新密钥并更新配置
   └→ 更新 config.yaml / 环境变量 / 凭据池
5. 复盘
   └→ 分析泄露原因，更新安全检查清单
```

### 3.4 当前环境已发现的密钥风险

> 在 `~/.hermes/config.yaml` 中检出以下需关注项：

| MCP 服务器 | 配置方式 | 风险等级 | 建议 |
|------------|---------|---------|------|
| obsidian | `OBSIDIAN_API_KEY` 明文在 `env` 中 | ⚠️ 中 | 改为环境变量引用 |
| github-gov1 | 通过 wrapper 脚本管理 | ✅ 可接受 | 确认脚本中无明文密钥 |

---

## 4. MCP 调用审计

### 4.1 审计日志字段

每次 MCP 工具调用应记录以下信息：

| 字段 | 说明 | 示例 |
|------|------|------|
| `timestamp` | 调用时间（ISO 8601） | `2026-06-17T10:30:00Z` |
| `mcp_server` | MCP 服务器名称 | `github-gov1` |
| `tool_name` | 调用的工具名 | `create_issue` |
| `user_prompt` | 触发调用的用户请求摘要 | "帮我创建 GitHub issue" |
| `args_hash` | 参数摘要（避免记录敏感数据） | `sha256(truncated_args)` |
| `duration_ms` | 调用耗时 | `2340` |
| `status` | 成功/失败/超时 | `success` |
| `error` | 错误信息（如有） | `connect_timeout` |
| `data_size` | 返回数据大小 | `12KB` |

### 4.2 异常检测规则

| 规则 | 触发条件 | 行为 |
|------|---------|------|
| 高频调用告警 | 同一 MCP 在 5 分钟内调用 > 50 次 | 暂停该 MCP，通知管理员 |
| 非工作时间调用 | 在 00:00-06:00 大规模调用 | 记录并告警 |
| 非常规工具调用 | MCP 暴露了 PRD 文档中未声明的工具 | 审查并确认是否被利用 |
| 敏感操作调用 | 调用了文件删除/写入/命令执行类工具 | 记录详细日志并通知 |
| 异常数据量 | 返回数据 > 10MB | 截断并告警 |

### 4.3 审计命令速查

```bash
# 查看 Hermes 运行日志中的 MCP 调用
grep -i "mcp" ~/.hermes/logs/*.log | grep "tool_call"

# 统计各 MCP 调用频率
grep "mcp_server" ~/.hermes/logs/*.log | awk '{print $NF}' | sort | uniq -c | sort -rn

# 检查失败的 MCP 连接
grep -i "error\|fail\|timeout" ~/.hermes/logs/*.log | grep -i "mcp"

# 检查是否有密钥泄露到日志
grep -i "api_key\|token\|secret\|password" ~/.hermes/logs/*.log
```

---

## 5. MCP 服务发现管控

### 5.1 接入流程

```
用户/开发 → 提出 MCP 接入请求
    ↓
安全基线检查（§2 安全检查清单）
    ↓
风险分级（§1）
    ↓
  ├── safe     → 直接配置 config.yaml，记录台账
  ├── work     → 审批通过后配置，API Key 托管凭据池
  └── risky    → 默认拒绝；特殊需求须沙箱化后临时启用
    ↓
配置记录台账（§5.2）
    ↓
纳入定期审计（§4）
```

### 5.2 配置台账记录

所有已接入 MCP 服务器需记录以下信息到统一台账：

| 字段 | 内容 |
|------|------|
| MCP 名称 | 如 `github-gov1` |
| 来源 | GitHub 仓库 / npm 包 / 自研脚本 |
| 版本/Commit | `v1.2.0` 或 `commit abc1234` |
| 接入日期 | 2026-01-15 |
| 风险等级 | safe / work / risky |
| 负责人 | 谁批准的接入 |
| 最后审计 | 2026-06-01 |
| 配置文件路径 | `config.yaml` 中的 MCP 块 |

### 5.3 白名单控制

- **stdin/stdout 模式**：确保 `command` 和 `args` 指向已知安全的可执行文件
- **HTTP/SSE 模式**：确保 `url` 指向白名单中的端点
- **禁止动态加载**：不通过用户输入动态拼接 `command`/`args`/`url`

### 5.4 定期扫描

```bash
# 列出所有已配置的 MCP 服务器
grep -A2 "mcp_servers:" ~/.hermes/config.yaml | grep -E "^\s+\w+:" | sed 's/://'

# 检查是否有多余/废弃的 MCP 配置
# 关注 enabled: true/false 状态
grep -B5 "enabled:" ~/.hermes/config.yaml | grep -E "(^\s+\w+:|enabled:)"
```

---

## 6. 禁止运行的 MCP 类型

以下类型的 MCP 服务器**明确禁止**接入，无论来源：

### 🔴 绝对禁止

| 类型 | 说明 | 风险 |
|------|------|------|
| **远程 Shell/命令执行** | 允许任意 Shell 命令执行的 MCP | 完全权限失控 |
| **未沙箱的文件系统 MCP** | 不限制可访问目录的文件系统 MCP | 数据泄露、文件破坏 |
| **密钥管理泄露型** | 在日志/响应中返回 API Key 的 MCP | 凭据泄露 |
| **未知来源的二进制 MCP** | 闭源、未审计、非官方分发的二进制文件 | 后门/恶意代码 |
| **加密货币挖矿** | 与加密货币相关的任何 MCP | 资源滥用、合规风险 |
| **P2P/网络穿透** | 建立反向隧道、内网穿透的 MCP | 内网暴露 |

### ⚠️ 严格受限（需额外审批）

| 类型 | 约束条件 |
|------|---------|
| **浏览器自动化** | 仅限沙箱化的 headless 模式，限制访问 URL 白名单 |
| **数据库直连** | 仅限只读用户、限制查询超时、限制返回行数 |
| **文件上传/下载** | 仅限指定目录、扫描恶意文件、限制文件大小 |
| **AI 模型执行** | 禁止本地加载任意模型，仅限托管 API |
| **社交平台发布** | 需用户手动确认每条发布内容（不允许静默发布） |

### 检查当前环境的「应禁止」MCP

```bash
# 扫描 config.yaml 中所有 MCP 的 command 和 args
# 报告任何指向 /bin/sh, /bin/bash, /usr/bin/python -c 等危险前缀的配置
grep -E "command:|args:" ~/.hermes/config.yaml | grep -E "(bash|sh|/tmp/|/dev/)" && echo "⚠️ 发现可疑配置"
```

---

## 附录

### A. 安全等级卡

```yaml
safe:
  action: auto-allow
  review: baseline-only
  audit: monthly-sample

work:
  action: require-approval
  review: full-checklist
  audit: weekly

risky:
  action: default-deny
  review: security-panel
  audit: per-call
```

### B. 快速参考：安全命令

```bash
# 1. 列出所有 MCP
grep -oP '^\s+\K\w+(?=:)' ~/.hermes/config.yaml | tail -n +$(grep -n "mcp_servers:" ~/.hermes/config.yaml | cut -d: -f1)

# 2. 检查是否有网络暴露的 MCP（含 url 字段）
grep -B3 "url:" ~/.hermes/config.yaml

# 3. 检查 env 中是否有敏感信息
grep -B5 -A2 "env:" ~/.hermes/config.yaml | grep -E "(KEY|TOKEN|SECRET|PASSWORD|API_KEY)" -i

# 4. 检查超时配置
grep -E "timeout:|connect_timeout:" ~/.hermes/config.yaml

# 5. 启动 MCP 安全审计
echo "=== MCP Security Audit $(date) ==="
echo "--- MCP Servers ---"
grep -oP '^\s+\K\w+(?=:)' ~/.hermes/config.yaml | tail -n +$(grep -n "mcp_servers:" ~/.hermes/config.yaml | cut -d: -f1)
echo "--- Network Exposure ---"
grep -B3 "url:" ~/.hermes/config.yaml || echo "(none)"
echo "--- Env Secrets ---"
grep -B5 -A2 "env:" ~/.hermes/config.yaml | grep -E "(KEY|TOKEN|SECRET)" -i || echo "(none found in sample)"
echo "=== Audit Complete ==="
```

### C. 相关技能

- [[linux-system-ops]] — 系统运维与日志审计基础
- [[hermes-evolution-mechanism]] — Hermes 机制理解（含 MCP 配置原理）
