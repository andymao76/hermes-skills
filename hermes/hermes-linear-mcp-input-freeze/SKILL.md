---
name: hermes-linear-mcp-input-freeze
category: hermes
description: 排查 Hermes 因 Linear MCP 初始化阻塞导致启动后键盘无法输入的问题
platform: Hermes Agent
severity: high
verified: true
author: Andy Mao
date: 2026-06-16
---

# Hermes Skill：Linear MCP 导致 Hermes 启动后无法输入问题排查与修复

## 问题现象

执行 `hermes` 后：
- Hermes 界面正常显示
- 键盘无法输入任何字符
- 回车无效
- 看起来像程序卡死
- MobaXterm 环境下表现最明显

## 环境信息

```
OS: Ubuntu 24.04.4 LTS
Hermes: v0.16.0
Client: MobaXterm
SSH: OpenSSH
TERM: xterm
```

## 排查过程

### 检查终端

```bash
echo $TERM
stty size
echo $SSH_CLIENT
echo $SSH_TTY
```

结果：TERM/TTY/SSH/窗口尺寸均正常。

### 对比测试

- Windows Terminal：正常输入
- MobaXterm：无法输入

## 根因分析

Hermes 启动流程中，MCP 初始化（含 OAuth Token 验证和握手）在主线程执行。当 Linear MCP 的 OAuth Token 异常、OAuth 状态异常、MCP 握手失败或响应异常时，可能导致主线程被阻塞。

典型表现：界面正常显示，但无法输入。

## 验证方法

禁用 Linear MCP 后 Hermes 恢复正常启动和输入，即可确认根因为 Linear MCP 初始化阻塞。

## 快速诊断命令

```bash
# 跳过用户配置启动（验证是否为 MCP 问题）
hermes --ignore-user-config

# 列出当前 MCP 服务
hermes mcp list

# 查找 Linear 相关配置
grep -R "linear" ~/.hermes

# 查看 MCP 连接日志
tail -200 ~/.hermes/logs/hermes.log
```

## 解决方案

### 方案1（推荐）
在 Hermes 配置中将 Linear MCP 的 `enabled` 设为 `false`。

### 方案2
删除失效的 OAuth Token 后重新授权。

### 方案3
仅在需要时启用 Linear MCP，平时禁用。

## 最佳实践

新增 MCP 后按以下流程验证：
1. 安装 MCP
2. 授权
3. 测试单独连接
4. 重载 MCP
5. 验证 Hermes 输入正常
6. 正式启用

## Learned Rule

```yaml
rule_name: hermes_mcp_startup_block_detection

trigger:
  - Hermes 启动后无法输入
  - TUI 正常显示
  - 最近新增 MCP
  - 最近执行 OAuth 授权

action:
  - 使用 `hermes --ignore-user-config` 测试
  - 禁用新增 MCP
  - 查看 MCP 日志（`tail -200 ~/.hermes/logs/hermes.log`）
  - 验证 OAuth 状态

conclusion:
  优先怀疑 MCP 初始化阻塞，而非终端或 SSH 问题。
```
