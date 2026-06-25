---
name: copilot-delegate
title: Copilot Delegate
description: 将编码/开发/GitHub任务委托给 Copilot CLI 执行，并自动归档结果到知识库
category: software-development
trigger: 当用户需要编写代码、修改项目、操作GitHub、创建脚本、开发MCP Server等开发任务时
version: 1.2
---

# Copilot Delegate

将编码/开发类任务委托给 **Copilot CLI** 执行，结果自动归档到知识库。

## 核心原则

```
Hermes = 思考者 + 知识管理者（第二大脑）
Copilot = 编码执行者（专业程序员）
```

**给 Copilot 干：** Lua开发 / Python脚本 / Shell脚本 / MCP Server开发 / Webhook开发 / GitHub项目维护  
**Hermes 自己干：** 知识管理 / 日报周报 / 排障经验 / 技能沉淀 / 系统运维

## 环境

- Copilot CLI 路径: `/home/andymao/.local/bin/copilot`
- 默认模型: `auto`（Copilot Auto 动态选择，非固定模型）
- Auto 模型池: GPT-5-mini / Claude 4.7 Opus / Claude Haiku 4.5 / Copilot 内部模型 (raptor-mini / oswe-vscode)
- 模型锁定: `copilot --model claude-sonnet-4` 或 `copilot --model gpt-5.2`
- VS Code Copilot Chat 同理，`copilot/auto` 动态选；可在聊天面板右下角手动锁定
- 非交互模式: `copilot -p "..." --allow-all-tools --silent`
- VS Code (snap) v1.124+ 内置 GitHub Copilot 扩展
- **模型发现方法**: 见 `references/copilot-model-discovery.md`

## VS Code 配合模式

用户同时拥有 **VS Code 内置 Copilot 扩展**（实时补全/内联聊天）和 **Copilot CLI**（批量代码生成）。两者不是替代关系，是互补：

```
┌──────────────────────────────────────────────────┐
│           三工具并行工作流                          │
│                                                    │
│  Hermes（终端）    VS Code + Copilot    Copilot CLI │
│  ┌────────────┐   ┌──────────────┐   ┌──────────┐ │
│  │ 知识管理    │   │ 实时补全      │   │ 批量生成  │ │
│  │ 方案设计    │   │ 内联聊天      │   │ 改项目    │ │
│  │ 排障        │   │ 逐行编码      │   │ Git操作   │ │
│  │ 归档        │   │              │   │ 脚本开发  │ │
│  └────────────┘   └──────────────┘   └──────────┘ │
└──────────────────────────────────────────────────┘
```

| 场景 | 用哪个 | 原因 |
|------|--------|------|
| 写一行函数、改个变量名 | VS Code Copilot 补全 | 实时，零切换 |
| 写一个新模块/文件 | VS Code Copilot 聊天 | 边看上下文边生成 |
| 批量重构（改整个项目） | Copilot CLI（Hermes 委托） | --allow-all-tools 全项目操作 |
| Git 操作（分支/commit/PR） | Copilot CLI（Hermes 委托） | 内建 GitHub MCP |
| 写独立脚本（Python/Shell） | Copilot CLI | 一行命令搞定 |
| 设计方案、调研技术 | 直接跟 Hermes 聊 | 知识库 + 搜索 |
| 调试排障 | 跟 Hermes 聊 | 系统工具 + 经验沉淀 |
| 写日报周报 | 跟 Hermes 聊 | 模板化流程 |

**典型配合流程：**
```
你在 VS Code 里写代码（Copilot 实时辅助）
   ↓ 遇到问题
问 Hermes: "这个 bug 怎么回事"
   ↓
Hermes 查知识库/搜方案 → 给你思路
   ↓
你在 VS Code 里修完代码
   ↓
"帮我 commit 并推送到 GitHub"
   ↓
Hermes 调 Copilot CLI → 提 PR → 归档到知识库
```

**注意：** VS Code 的 Copilot 扩展消耗的是 GitHub Copilot 许可证额度；Copilot CLI 消耗的是 AI Credits/配额。两者计费独立，不要互相替代。

## 调用方式

### 1. 基础委托（非交互，自动退出）

```bash
copilot -p "任务描述" --allow-all-tools --silent
```

- `-p` 直接传入提示，执行完自动退出
- `--allow-all-tools` 自动批准所有工具（文件读写、Shell 命令、Git 操作）
- `--silent` 只输出回答，不含统计信息

### 2. 指定工作目录

```bash
copilot -p "任务描述" -C /path/to/project --allow-all-tools --silent
```

### 3. 全权限模式（等效 --allow-all-tools + --allow-all-paths + --allow-all-urls）

```bash
copilot -p "任务描述" --yolo --silent
```

### 4. 计划模式（先生成方案，不执行）

```bash
copilot -p "分析项目结构并设计方案" --plan --allow-all-tools --silent
```

### 5. 交互模式（需要手动操作时通知用户）

```
用户自己执行: copilot
进入后使用 /plan、/fix、/explain、/model 等命令
```

## 触发判断矩阵

| 任务类型 | 委托给 Copilot? | 说明 |
|----------|----------------|------|
| Lua 插件开发 | ✅ 委托 | Copilot 分析代码库后编写 |
| Python 脚本 | ✅ 委托 | 单文件或模块均可 |
| Shell 脚本 | ✅ 委托 | 系统管理、巡检、部署 |
| MCP Server 开发 | ✅ 委托 | 标准 MCP 协议实现 |
| Webhook 开发 | ✅ 委托 | Flask/FastAPI/Express |
| GitHub PR/Issue | ✅ 委托 | copilot 内建 GitHub MCP |
| Git 操作 | ✅ 委托 | commit/branch/merge |
| 代码审查 | ✅ 委托 | analyze / review |
| 知识库查询 | ❌ 自理 | Hermes 知识库更快 |
| 系统排障 | ❌ 自理 | Hermes 运维工具更强 |
| 日报周报 | ❌ 自理 | 模板化流程 |
| 消息发送 | ❌ 自理 | Hermes 多平台 |
| 简单文件读写 | ❌ 自理 | 直接 tools 更高效 |

## 标准委托流程

```
用户请求
  ↓
Hermes 判断: 是否编码/开发类任务?
  ↓ 是
Hermes 拆解需求 → 明确范围 → 确定工作目录
  ↓
terminal("copilot -p '需求描述' -C <workdir> --allow-all-tools --silent")
  ↓
Copilot 分析项目 → 修改代码 → 运行测试 → 输出结果
  ↓
Hermes 验证结果（检查文件变更、运行状态）
  ↓
Hermes 归档到知识库（~/knowledge/工作/脚本/ 或对应项目目录）
  ↓
告知用户完成情况
```

## 常见场景模板

### 场景1：写一个Python脚本

```
用户：写一个Kafka消费延迟巡检脚本

→ Hermes 拆解：连接Kafka、获取consumer group lag、输出格式化报告
→ Copilot CLI:

copilot -p "
在 ~/scripts/ 下创建一个Kafka消费延迟巡检脚本 kafka-lag-check.py

要求：
- 使用 Python 3 + kafka-python 库
- 连接指定的bootstrap-server
- 列出所有consumer group及其lag
- 输出格式化的表格报告
- 支持 --threshold 参数（默认1000）告警
- 添加 usage 和 --help
" --allow-all-tools --silent

→ Hermes 验证脚本可运行
→ 保存到知识库 scripts/ 目录
```

### 场景2：Lua插件开发

```
用户：给 Nginx 写一个限流 Lua 插件

→ Copilot CLI:

copilot -p "
分析 /etc/nginx/ 下的配置结构，
在 /etc/nginx/lua/ 下创建限流插件 limit-rate.lua

要求：
- 基于 lua-resty-limit-traffic
- 支持 IP 维度和 URL 维度限流
- 可配置 QPS 阈值
- 错误时返回 429 + JSON body
- 日志记录被限流的请求
" -C /etc/nginx --allow-all-tools --silent
```

### 场景3：MCP Server

```
用户：开发一个天气查询 MCP Server

→ Copilot CLI:

copilot -p "
在 /home/andymao/projects/weather-mcp/ 下创建一个 MCP Server

要求：
- Python + FastMCP
- 工具: get_weather(city), get_forecast(city, days)
- 使用天气API（配置在环境变量 WEATHER_API_KEY）
- 添加 setup.py 和 README.md
- 符合 MCP 协议规范
" -C /home/andymao/projects/weather-mcp --allow-all-tools --silent
```

### 场景4：GitHub操作

```
用户：给 andymao76/xxx 仓库提 PR

→ Copilot CLI:

copilot -p "
在 ~/projects/xxx 仓库中：
1. 从 main 创建分支 feature/add-logging
2. 在 src/main.py 中添加结构化日志
3. 提交并推送到 GitHub
4. 创建 PR 描述变更内容
" -C ~/projects/xxx --allow-all-tools --silent
```

### 场景5：运行 /plan 模式做设计

```
用户：帮我分析这个项目的架构，给出重构建议

→ Copilot CLI:

copilot -p "
分析当前项目结构，给出架构分析和重构建议，包括：
1. 目录结构分析
2. 模块依赖关系
3. 代码质量问题
4. 重构优先级排序
" -C /path/to/project --plan --allow-all-tools --silent
```

## 结果归档规范

Copilot 执行完毕后，Hermes 验证结果并归档：

1. **脚本类** → `~/knowledge/工作/脚本/{名称}/`
2. **项目类** → 原项目目录（Copilot 已直接修改）
3. **知识点** → `~/knowledge/技能/{领域}/` + 关联到相关笔记
4. **归档后** → 执行 `cd ~/knowledge && enzyme refresh` 刷新索引

## 注意事项

- ❗ Copilot CLI 耗用 AI Credits（配额制），非编码任务不要滥用
- ❗ 大型项目首次委托时指定 `-C` 工作目录，让 Copilot 理解项目上下文
- ❗ `--allow-all-tools` 相当于给 Copilot 完全控制权，信任但验证
- ❗ 对于需要多个步骤的复杂任务，先让 Copilot 用 `--plan` 出方案，再执行
- ✅ 验证输出时关注：文件是否生成、语法是否正确、测试是否通过
- ✅ 结果归档到知识库前，先提取关键信息（组件名、API、配置等）

### ⚠️ Hermes 安全拦截坑

从 Hermes 内部调用 `copilot -p "..." --allow-all-tools --silent` **可能** 触发 Hermes 安全策略拦截（`BLOCKED: User denied this command`）。因为 `--allow-all-tools` 被识别为高风险参数。

**实测结果（2026-06-11）：** 调用 `copilot -p '创建 hello.py 打印 1-100 的和' --allow-all-tools --silent` 成功通过，未被拦截。简单编码任务通常不会被拦截。

三种应对方式：

1. **让用户自己在终端执行** — 把完整的 copilot 命令+prompt 给用户，让他们贴到终端运行
2. **先用 `--plan` 模式** — 只设计方案不执行文件操作，安全策略通常放行：`copilot -p "..." --plan --silent`
3. **对已知安全的命令，用户可以开 `hermes --yolo`** 绕过审批（不推荐长期开启）

**注意：** 拦截后提示 "Do NOT retry this command" 时，不要用不同措辞重试同一命令——换别的方案（比如让用户自己执行，或者改用 --plan 模式）。

## 本地项目发现

委托编码任务前，需要先知道用户有哪些项目。有两种系统化方法：

1. **VS Code 工作区检查** — 详情见 `references/vscode-project-discovery.md`
2. **常见项目目录扫描** — 检查 `~/projects/`, `~/code/`, `~/dev/`, `~/src/`, `~/work/` 等目录

对发现的每个项目，简述其目的、技术栈和代码量，让用户确认后再委派 Copilot。
