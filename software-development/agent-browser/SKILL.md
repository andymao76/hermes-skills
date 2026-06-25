---
name: agent-browser
description: "Browser automation agent — navigate, fill forms, click, screenshot, extract JS-rendered content, manage cloud sessions. Use when user needs to automate web interaction, scrape dynamic pages, test UIs, or take screenshots. 423K+ installs on skills.sh. From Vercel Labs."
version: 1.0.0
author: Vercel Labs
license: MIT
metadata:
  hermes:
    tags: [browser, automation, scraping, testing, e2e]
    related_skills: [playwright, puppeteer]
---

# Agent Browser

Browser automation skill from Vercel Labs. Supports headless Chromium, real Chrome with profiles, and cloud-hosted remote browsers.

## Key Capabilities

1. **Navigation** — navigate to URLs, wait for load, handle redirects
2. **Page Inspection** — get HTML, text, screenshots, console logs
3. **Interactions** — click, type, select, hover, scroll, file upload
4. **Data Extraction** — structured JSON extraction, table parsing, markdown conversion
5. **JavaScript Execution** — run custom JS in page context
6. **Session Management** — persistent sessions, cookies, localStorage
7. **Cloud Browsers** — remote browser instances for parallel execution

## Installation

```bash
# 1. Install the CLI (use user-local prefix to avoid sudo)
npm config set prefix ~/.npm-global
export PATH=~/.npm-global/bin:$PATH
npm install -g agent-browser

# 2. Install Chrome browser for automation
agent-browser install

# Optional: install system dependencies if Chrome fails to launch
agent-browser install --with-deps
```

## Usage with Hermes

```bash
# agent-browser 是独立 CLI，通过 terminal 工具调用
export PATH=~/.npm-global/bin:$PATH

# 导航
agent-browser open https://example.com

# 截图
agent-browser snapshot -i          # 获取交互元素快照
agent-browser screenshot out.png   # 截图

# 关闭浏览器
agent-browser close
```

> 注意：agent-browser 通过 CDP 协议直接控制 Chrome，不使用 Playwright/Puppeteer。
> Hermes 内置的 browser_navigate/browser_click 等工具是独立实现，与 agent-browser 无关。

## Built-in Skills

The CLI ships with version-matched skills accessible via `agent-browser skills list`:

| Skill | Purpose |
|-------|---------|
| `core` | 核心使用指南（snapshot-and-ref 工作流、交互、提取、截图） |
| `agentcore` | AWS Bedrock AgentCore 云端浏览器 |
| `dogfood` | Web 应用探索性测试、找 bug |
| `electron` | Electron 桌面应用自动化（VS Code, Slack, Discord, Figma） |
| `slack` | Slack 工作区交互 |
| `vercel-sandbox` | Vercel Sandbox 微虚拟机中运行 |

加载技能内容：`agent-browser skills get <name> --full`

## Pitfalls

- **无 `--headless` 标志**：headless 是默认行为，`--headed` 才显示窗口。使用 `--headless` 会导致命令静默挂起。
- **首次 `open` 需充足超时**：Chrome 冷启动需要时间，`terminal(timeout=30)` 或更长。
- **Snap 安装的 Node.js** 下 `npm install -g` 写到 `/usr/local/lib` 会权限拒绝。解决：`npm config set prefix ~/.npm-global`。
- **Chrome 单独下载**：`agent-browser install` 下载 Chrome for Testing 到 `~/.agent-browser/browsers/`。仅 `npm install -g` 不够。
- **依赖库缺失**：Linux 上 Chrome 可能报 shared library 错误，用 `agent-browser install --with-deps` 安装系统依赖。
- **与 Hermes 内置 browser 工具无关**：`browser_navigate`/`browser_click` 是 Hermes 自己的实现，不走 agent-browser。

## Common Use Cases

- Price monitoring and competitive tracking
- Form automation and data entry
- Screenshot generation for reporting
- JS-heavy page content extraction
- E2E UI testing
- Login-gated portal data access
