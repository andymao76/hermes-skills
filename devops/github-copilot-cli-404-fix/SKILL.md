---
name: github-copilot-cli-404-fix
description: GitHub Copilot CLI 认证失败(404)排查与修复 — 检查 gh 状态、安装 Copilot CLI、处理 GITHUB_TOKEN 冲突、确认订阅
trigger: Copilot CLI 认证失败、Copilot 404、gh copilot unknown command、Copilot subscription not found
category: devops
---

# GitHub Copilot CLI 认证失败（404）修复指南

## 问题现象

Copilot CLI 报错：
```
Copilot CLI authentication failed
404 Not Found
You are not authorized for Copilot
```
或：
```
Copilot subscription not found
```

## 排查步骤

### 1. 检查 GitHub 登录状态
```bash
gh auth status
```
期望：`Logged in to github.com account andymao76`

### 2. 检查 gh 是否支持 copilot
```bash
gh copilot status
```
如果返回 `unknown command "copilot"` → Copilot CLI 未安装

### 3. 检查 Node 环境
```bash
node -v  # 期望 v24.15.0+
npm -v   # 期望 11.12.1+
```

## 解决方案

### 安装新版 Copilot CLI
```bash
npm install -g @github/copilot
```

权限问题：
```bash
sudo npm install -g @github/copilot
```

scripts 被禁用：
```bash
npm_config_ignore_scripts=false npm install -g @github/copilot
```

### 验证安装
```bash
copilot --version
```

### 重新认证
```bash
unset GITHUB_TOKEN GH_TOKEN
gh auth logout
gh auth login --web
```

### 检查订阅
访问 https://github.com/settings/copilot
- 显示 `Start free trial` → 无订阅，需开通
- 显示 `Copilot Pro/Business` → 已具备权限

## 最终验证
```bash
copilot
```
正常进入交互界面即修复成功。

## 根因分析

本案例原因：
- GitHub CLI 已登录成功
- gh 未安装 Copilot CLI（`npm install -g @github/copilot`）
- Node 环境正常
- 安装新版 `@github/copilot` 后恢复

## 经验总结

遇到 `Copilot CLI authentication failed` + `404 Not Found`，优先检查：
1. GitHub 登录状态
2. Copilot CLI 是否安装
3. Copilot 订阅是否有效
4. GITHUB_TOKEN 是否干扰 OAuth 登录
5. Node/npm 环境是否正常

## ACP 集成

当通过 `delegate_task(acp_command="copilot")` 调用 Copilot 时，子进程会继承 `GITHUB_TOKEN` 经典 PAT 导致认证失败。

**解决方案：** 使用 ACP 包装器清除环境变量中的经典 PAT。
详见 `references/acp-wrapper-patch.md`。
