# 飞书/Feishu/Lark 连接方案参考

> 2026-06-08 调研整理。涵盖 Hermes 原生接入、Lark MCP Server、Feishu CLI、OpenClaw、LangBot 五条路径。

## 方案对比总览

| 方案 | 接入方式 | 适用场景 | 复杂度 | 维护方 |
|------|---------|---------|--------|--------|
| **Hermes Gateway 原生** | 飞书开放平台应用 + config.yaml 配凭证 | 仅消息收发(bot) | 低 | NousResearch |
| **Lark OpenAPI MCP** | npx @larksuiteoapi/lark-mcp | 深度飞书能力(文档/日历/审批等) | 中 | 飞书官方 |
| **Feishu CLI** | npm install -g feishu-cli | CLI 式操作 + AI Agent 技能 | 低 | 飞书官方/社区 |
| **OpenClaw** | openclaw 平台配置飞书 channel | 多通道中央管理 | 中 | OpenClaw |
| **LangBot** | LangBot 内置飞书适配器 | 快速搭建 AI Bot | 低 | LangBot |

## Hermes Agent 飞书 Gateway 接入

Hermes Agent 将飞书作为消息通道原生支持，使用 `hermes gateway setup` 交互式向导配置。

**步骤简述：**
1. 登录 [飞书开放平台](https://open.feishu.cn/) → 控制台
2. 创建企业自建应用 → 添加机器人能力
3. 配置权限：`im:message`, `im:resource` 等
4. 获取 App ID + App Secret → 填入 Hermes gateway 向导
5. 配置事件订阅（Webhook URL 由 Hermes gateway 向导提供）
6. 发布应用 → 企业管理员审批

**参考文章：**
- Hermes Agent 飞书接入完全教程（知乎）
- Hermes Agent 飞书接入指南（腾讯云开发者）

## Lark MCP Server 配置示例

```yaml
mcp_servers:
  lark-mcp:
    command: npx
    args:
      - -y
      - @larksuiteoapi/lark-mcp
      - mcp
      - -a
      - cli_xxxxx           # App ID
      - -s
      - xxxxxxxxxx          # App Secret
```

**用户身份模式（OAuth，额外步骤）：**
```bash
# 1. 先登录获取 user_access_token
npx -y @larksuiteoapi/lark-mcp login -a cli_xxxxx -s xxxxxxx

# 2. 配置中加 --oauth --token-mode user_access_token
```

**工具预设选择（-t 参数）：**
| 预设 | 包含工具 |
|------|---------|
| `preset.im.default` | 消息相关工具 |
| `preset.document.default` | 文档相关工具 |
| `preset.calendar.default` | 日历相关工具 |
| `preset.all` | 全部工具（默认） |

## Feishu CLI 快速安装

```bash
npm install -g feishu-cli

# AI Agent 技能文件（Claude Code 等用）
feishu-cli skill list    # 查看可用技能
feishu-cli skill install <name>  # 安装技能
```

**覆盖的 11 大业务域：**
消息、文档、日历、邮件、审批、任务、搜索、通讯录、知识库、云盘、多维表格

## 关键决策点

**什么时候用 Hermes Gateway（消息通道） vs Lark MCP Server：**

- 只需要 bot 收发飞书消息 → **Hermes Gateway**
- 需要读写文档、管理日历、审批流程等 → **Lark MCP Server**（可叠加使用）
- 不需要 Hermes，只要在 Claude Code/Cursor 里操作飞书 → **Feishu CLI**
- 两套可以共存：Gateway 做消息通道，MCP 做深度工具

## 注意事项

- 国内版(open.feishu.cn)和国际版(open.larksuite.com)的 App 不能混用
- 飞书开放平台的 App 需要**企业管理员审批**发布后才能使用 bot 能力
- npx 在代理环境下第一次启动较慢(10-30s) — 推荐 `npm install -g @larksuiteoapi/lark-mcp` 后直连 node
- lark-mcp 目前不支持的：文件上传/下载、云文档直接编辑（只能导入/读取）
