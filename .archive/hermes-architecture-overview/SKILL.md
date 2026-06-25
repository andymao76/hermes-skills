---
name: hermes-architecture-overview
description: "Generate a full-system architecture snapshot of the Hermes Agent installation — covers config, providers, gateway, MCP servers, skills, memory, knowledge base, cron jobs, and ports. Produces structured Chinese markdown + Excalidraw diagram."
version: 1.0.0
author: agent-created
tags: [hermes, architecture, overview, diagnostics, system-dump]
related_skills: [hardware-diagnostics, hermes-system-maintenance]
---

# Hermes Agent 系统架构快照

输出当前 Hermes Agent 系统的完整架构图，涵盖 8 个维度：核心推理配置、系统服务/端口、消息网关、MCP 生态、技能库、存储与记忆系统、知识库、定时任务。

## 触发条件

- "输出系统架构图"
- "系统全景" / "系统概况"
- "列一下当前所有组件"
- "当前系统状态综述"
- "输出架构快照"

## 前置约束

- 需要 `hermes --version` 可执行
- 需要访问 `~/.hermes/config.yaml`（敏感 key 需在输出中脱敏）
- 需要 `sqlite3` 访问 `state.db` 和 `memory_store.db`
- 需要 `skills_list` 工具获取完整技能列表

## 工作流

### 第一步：采集数据

参考 `references/full-system-snapshot.md` 中的探测命令，并行收集 8 个维度的数据：

1. **核心推理层** — `hermes --version`、config.yaml 中的 model/default provider
2. **系统服务** — systemctl 列出 hermes-gateway、hermes-bridge 等
3. **端口监听** — ss -tlnp 过滤关键端口
4. **MCP 服务器** — config.yaml 的 mcp_servers 段
5. **技能库** — skills_list 获取全部技能及其分类
6. **存储与记忆** — memory_store.db、knowledge/ 目录、MEMORY.md/USER.md
7. **会话数据库** — state.db 的消息/会话数
8. **定时任务** — cron/jobs.json 的内容

### 第二步：生成结构化报告

按以下格式输出中文报告（分节 + 表格）：

```markdown
## 核心推理层
| 维度 | 详情 |

## 系统服务
| 服务 | 端口 | 状态 |

## 消息网关
- 微信 — 状态
- Telegram — 状态
- Discord — 状态
... 其他平台

## MCP 服务器
| MCP | 协议 | 功能 |

## Skills 技能库
总计：N 技能，分类统计

## 存储与记忆
| 系统 | 数据量 |

## Cron 定时任务
| 任务 | 时间 | 类型 | 推送目标 |

## 架构图
→ 文件路径
```

### 第三步：生成 Excalidraw 架构图

使用 Excalidraw skill 和以下配色约定：

- 蓝色 #a5d8ff — 核心推理 / 技能
- 绿色 #b2f2bb — 交互层 / 定时任务
- 紫色 #d0bfff — 网关 / 平台适配
- 橙色 #ffd8a8 — 外部服务 / 代理
- 黄色 #fff3bf — MCP 服务器
- 青色 #c3fae8 — 存储 / 记忆 / 知识库
- 红色 #ffc9c9 — 关键服务（代理等）

垂直布局顺序（两列，左宽右窄）：核心推理层 → 消息网关 → MCP 生态 → Skills → Cron | 会话交互层 → 外部服务 → 存储系统 → 图例

### 布局密度要求

架构图包含 65+ 元素，必须紧凑排布以满足 A3 画布。关键参数：
- 标题 fontSize=22，板块标题 fontSize=16，框内文本 fontSize=11-13
- 矩形最小尺寸可降为 55×45
- 左右两列：左列 430px，右列 480px
- MCP 部分排成 2×3 网格
- 渲染时必须使用 rsvg-convert 管线（CairoSVG 不兼容 CJK），详见 excalidraw 技能的 `references/render-to-png.md`

✅ 字体缩放指南（可接受范围）：
- 标题 22、副标题 12、板块标题 16、框内 11-13、图例 13
- 更小的字体 = 更多内容可容纳，但确保最终用 librsvg 渲染

⚠️ 用户反馈"字堆在一起"时：
1. 不要调整字体大小或元素间距
2. 立即切换到 SVG→rsvg-convert CJK 渲染管线

## 陷阱

### config.yaml key 泄露
在展示 config.yaml 内容时必须脱敏 api_key 字段。仅显示模型/provider 配置结构。

### Gateway 平台状态
Gateway 会注册所有配置的平台适配器，即使某些平台未连接也会显示"可用"。通过 `send_message(action='list')` 或检查平台具体连接状态来区分"在线"和"已注册"。

### 知识库文件数
`find ~/knowledge/ -type f | wc -l` 是快速统计，但大的 articles_baidu 目录可能主导数字。按子目录分解统计更有意义。

### state.db 权限
Hermes 运行时的 state.db 可能有 WAL 锁。如果 `COUNT(*)` 返回空，检查 db-shm 和 db-wal 文件是否存在。

### Cron job 状态字段
`last_status: null` 表示从未运行过（如新建的任务），不是错误。`last_status: "error"` 才表示上次运行失败。

## 参考资料

- `references/full-system-snapshot.md` — 完整的探测命令集合
