---
name: hermes-agent-evolution-mechanism
description: 将Hermes Agent从聊天工具进化为会工作、会记录、会总结、会复用、会自我优化的个人AI操作系统
version: 1.1.0
author: andy
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [hermes, evolution, knowledge, workflow, optimization]
---

# Hermes Agent 进化机制

将 Hermes Agent 从"聊天工具"进化为：

> 会工作、会记录、会总结、会复用、会自我优化的个人 AI 操作系统。

## 总体进化闭环

Hermes 每次处理问题时，应尽量形成以下闭环：

```
问题输入 → 分析与执行 → 解决方案 → 经验总结 → 写入 Knowledge → 提炼 Skill → 未来自动复用
```

**核心原则：** 每解决一次问题，都要让 Hermes 变得更聪明一点。

## 任务后沉淀规则

### 故障排查类
触发条件：Linux报错 / MCP连接失败 / IM平台异常 / 大数据组件故障 / 协议解析问题
沉淀路径：`~/knowledge/skills/troubleshooting/`
命名规则：`YYYYMMDD_关键词_fix.md`

### 运维流程类
触发条件：巡检/启停/日志分析/健康检查
沉淀路径：`~/knowledge/skills/bigdata/`、`~/knowledge/skills/linux/`、`~/knowledge/skills/hermes/`

### 项目经验类
触发条件：项目跟进/客户分析/状态更新/会议纪要
沉淀路径：`~/knowledge/projects/项目名/`，同步更新 `~/knowledge/_system/project_status.yaml`

## FEISHU/WhatsApp 输入分类

| 类型 | 关键词 | 保存路径 |
|------|--------|----------|
| 临时想法 | `记录：` | `~/knowledge/inbox/quick_notes/YYYY-MM-DD.md` |
| 故障经验 | `经验：` | `~/knowledge/skills/`（按分类） |
| 项目进展 | `项目：` | `~/knowledge/projects/项目名/worklog.md` |

## 知识库推荐结构

```
~/knowledge/
├── _system/          # 项目状态、规则、进化日志
├── worklog/          # 日报/周报/月报
├── skills/           # 技能沉淀（hermes/linux/bigdata/telecom/li-hi2/troubleshooting）
├── projects/         # 项目经验
├── bigdata/          # HDFS/YARN/Hive/HBase/Kafka/Flink/Greenplum/Ambari
├── telecom/          # 核心网/SIP RTP/LI/Wireshark
└── inbox/            # 收件箱（feishu/whatsapp/quick_notes）
```

## 周期性优化

| 周期 | 动作 | 输出 |
|------|------|------|
| 每日 | 整理inbox，归档到worklog/skills/projects | `worklog/daily/YYYY-MM-DD.md` |
| 每周 | 执行 curator，合并/清理/分类 | `_system/evolution_log.md` |
| 每月 | 生成能力报告 | `_system/monthly_evolution_report_YYYY-MM.md` |

## 项目状态中心

Hermes 每次涉及项目类任务时，应优先读取 `~/knowledge/_system/project_status.yaml`，更新项目状态和下一步动作。项目名中的斜杠对应 knowledge/projects/ 下的子目录。

**行为规则：** 当用户提到项目名（如 A1、丢丢、Second Brain 等），先查 project_status.yaml 了解当前优先级和 next_action，再执行任务。任务完成后更新 project_status.yaml 中的状态和 next_action。

**⚠️ 常见陷阱（2026-06-22 经验）：** 当用户询问项目状态时，**仅靠 project_status.yaml 可能已过时**（如美签项目 status=yaml 显示 waiting，实际已面签被拒）。正确做法：
1. 先查 project_status.yaml → 获取 project 基线状态
2. **再查 session_search** → 用户可能已在更早会话中提过更新
3. **最后再看 worklog.md** → 实际进展记录
4. 三方交叉验证后再输出，不要单凭 yaml 就下结论

## Cron Job 管理规范

Hermes 的定时任务使用 `cronjob` 工具管理。关键要点：

| 要素 | 说明 |
|------|------|
| 任务名 | 中文名，清晰标识用途 |
| 调度 | 标准 cron 格式 `分 时 日 月 周` |
| 投递 | `origin`=回当前频道, `deliver`=指定平台 |
| 状态跟踪 | `last_status=ok` 正常执行, delivery_error 需关注 |

**提醒时间 vs 动作时间分离模式（丢丢服药提醒实践）：**
- 提醒时间（cron trigger）≠ 动作截止时间（prompt 中写明）
- 例：cron `0 8 * * *` 推送提醒，prompt 中写"请在 **8:40** 前喂药"
- 好处：用户有缓冲期，可调整实际动作时间而无需改 cron
- 注意：prompt 内容中的时间描述也要一并更新

## API Key 提取规范（Bailian / 自定义 Provider）

当 Provider 使用 `api_key_env`（而非直接 `api_key`）时，Python 脚本中 `os.environ.get(env_var)` 可能为空（终端 session 未加载 .env）。**正确做法是读 .env 文件：**

```python
# Bad: 依赖环境变量（终端 session 未加载）
api_key = os.environ.get('DASHSCOPE_API_KEY', '')  # ← 可能为空

# Good: 直接从 .env 文件读取
def get_key_from_env(env_var):
    env_path = os.path.expanduser('~/.hermes/.env')
    if not os.path.exists(env_path):
        return ''
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line.startswith(env_var + '='):
                parts = line.split('=', 1)
                if len(parts) == 2 and parts[1]:
                    return parts[1].strip("'\" ")
    return ''
```

此模式适用于所有使用 `api_key_env` 的 provider（如 bailian/DASHSCOPE_API_KEY）。

## 7 阶段进化路线图（Roadmap）

### Phase 1：知识中台（Knowledge Platform）
**目标：** 建立统一知识中心，形成"问题→解决→总结→Skill→Knowledge"闭环  
**当前进度：** **✅ 85%**
| 子项 | 状态 | 说明 |
|------|------|------|
| knowledge/ 目录标准化 | ✅ | skills/projects/troubleshooting/telecom/bigdata 已就位 |
| _system/ 项目状态管理 | ✅ | project_status.yaml 管理17个活动项目 |
| decision_log 决策日志 | ✅ | 已收录9条关键决策 |
| inbox 输入分类 | 🔄 半自动 | 飞书/WeChat输入→knowledge 链路待完善 |

### Phase 2：Skill 自动工厂（Skill Auto Factory）
**目标：** 每次故障解决自动沉淀为可复用 Skill，累积 1000+ Skill  
**当前进度：** **🔧 40%**
| 子项 | 状态 | 说明 |
|------|------|------|
| 排错→Skill 手动流程 | ✅ | 本周已沉淀 5 个新技能 |
| 排错→Skill 自动流程 | ❌ | 待实现自动检测→生成管道 |
| SKILL.md 标准化 | ✅ | Hermes 官方格式已锁定 |
| curator 定期整理 | 🔄 已配置 | 需验证实际运行效果 |

### Phase 3：运维专家 Agent（Ops Agent）
**目标：** 自动巡检系统/网络/Gateway/Docker/MCP/IM平台/腾讯云，异常→告警  → 修复建议  
**当前进度：** **✅ 100%（原型完成）**

| 子项 | 状态 | 说明 |
|------|:----:|------|
| `ops_agent.py` 每日巡检脚本 | ✅ | 覆盖 7 大维度（系统/网络/Gateway/Docker/MCP/IM/腾讯云） |
| 运维日报 cron 每日 09:00 | ✅ | 自动执行 → `worklog/daily_health/` → 异常推送 |
| 结构化报告模板 | ✅ | 表格化 + 维度分节 + 异常摘要 |
| 异常自动告警 | ✅ | 异常项在报告中高亮，cron投递到聊天 |
| 融入已有大数据技能 | 🔄 | 9个大数据技能 (120+操作模式) 可作为 Ops Agent 的知识后盾 |

### Phase 4：通信专家 Agent（Telecom Agent）
**目标：** 上传 PCAP → 自动分析 → 自动报告，覆盖 ETSI/3GPP/HI2/ASN.1/SIP-I/RTP  
**当前进度：** **⏳ 15%**

已有基础技能矩阵但距离 Agent 化较远：
| 子项 | 状态 | 说明 |
|------|------|------|
| huawei-hi2 / zte-li | ✅ | 合法监听协议技能 |
| wireshark-lua | ✅ | 插件开发技能 |
| tcpdump-analysis | ✅ | 抓包分析技能 |
| asn1-codec | ❌ 待安装 | ASN.1 编解码 |
| 3gpp-expert | ✅ | 3GPP 标准体系 |
| 自动 PCAP 分析管道 | ❌ | 需搭建 |
| 自动报告生成 | ❌ | 需开发 |

### Phase 5：项目管理 Agent（Project Agent）
**目标：** 自动跟踪项目状态，生成 weekly_report / next_action  
**当前进度：** **🔧 25%**
| 子项 | 状态 | 说明 |
|------|------|------|
| project_status.yaml | ✅ | 17个项目状态管理 |
| 日报生成 | ✅ | 工作日 17:40 cron 提醒 |
| 周报生成 | 🔄 待优化 | 手动触发，未自动化 |
| 月报生成 | ❌ | 未实现 |
| Apple Notes 同步 | ❌ | 待回家部署 |

### Phase 6：第二大脑同步（Second Brain Sync）
**目标：** Feishu/WeChat/WhatsApp → Hermes → Knowledge → Apple Notes → iPhone  
**当前进度：** **🔧 80%**

| 子项 | 状态 | 说明 |
|------|:----:|------|
| Feishu 输入 → Inbox | ✅ | `feishu_to_inbox.py` — 收到关键词消息自动保存 |
| WeChat 输入 → Inbox | ✅ | 同脚本，source=wechat |
| WhatsApp 输入 → Inbox | ✅ | 同脚本，source=whatsapp |
| Inbox → Knowledge 自动归档 | ✅ | `inbox_sorter.py` — cron 每日 22:30 自动分类 |
| 分类规则（记录→worklog/daily/） | ✅ | 完整分类规则见 `references/inbox-automation.md` |
| Apple Notes→iPhone | ❌ | 等待 mcp 方案 |
| 关键字触发：记录/项目/故障/经验 | ✅ | Hermes 会话中识别关键词自动触发保存 |

### Phase 7：多 Agent 协作（Multi-Agent）
**目标：** Manager Agent → 分派 → 专业 Agent 协作 → 汇总  
**当前进度：** **❌ 5%**

Hermes 已有 delegate_task（子代理并行）和 kanban（多 profile 协作）能力，但尚未组建专用 Agent 团队。

| 角色 | 状态 | 说明 |
|------|------|------|
| Manager Agent | ❌ | 未实现 |
| Ops Agent | ❌ | delegate_task + 大数据skills可快速搭建 |
| Telecom Agent | ❌ | 需先完成 Phase 4 知识沉淀 |
| Knowledge Agent | ❌ | curator 可部分承担 |
| Report Agent | ❌ | 需整合日报/周报/月报生成 |

---

## 进化优先级（更新版）

| 优先级 | 阶段 | 行动 | 预计耗时 |
|:------:|:----:|------|:--------:|
| **P0** | Phase 1~2 收尾 | 完善 knowledge 自动化、建立排错→Skill 管道 | 2~3 天 |
| **P1** | Phase 3~4 启动 | Ops Agent 原型 + Telecom 知识矩阵完善 | 1~2 周 |
| **P2** | Phase 5~6 同步 | Project Agent 自动化 + Apple Notes 同步 | 1 周 |
| **P3** | Phase 7 聚合 | Multi-Agent 协作架构上线 | 2~4 周 |
| **P∞** | 长期 | Hermes OS — 个人通信/大数据/运维/秘书专家 | 持续进化 |

## 相关技能

| 技能 | 关系 |
|------|------|
| `second-brain` / `hermes-second-brain-v5` | 侧重建脑知识管理（Obsidian/Inbox/双向链接），本skill侧重Hermes自动进化闭环 |
| `hermes-agent` | Hermes Agent配置/使用/排障，本skill是它的"运维运营"层面 |
| `self-improvement` | 捕获学习经验，本skill是更高层的进化策略框架 |

## Support Files

### references/
- `domestic-vision-providers.md` — 国内AI视觉模型调用方案（阿里百炼Qwen-VL + SiliconFlow Qwen3-VL），适用场景：主力模型不支持视觉时的备份方案
- `inbox-automation.md` — Inbox 自动归档管线完整文档：feishu_to_inbox.py + inbox_sorter.py 的关键词规则、调用方法、cron 配置
- `ops-agent-daily-check.md` — Ops Agent 每日巡检文档：7 大检查维度、阈值、ops_agent.py 调用方式、报告格式

### templates/
- `session-knowledge-deposit.md` — 每次任务后的知识沉淀检查清单，覆盖：project_status更新、decision_log追加、skills提炼、memory更新、cron调整

### scripts/
- `batch-vision-scan.py` — 批量图片视觉扫描模板，支持百炼/SiliconFlow双provider，含断点续扫、结果缓存、自动重试

## 实践记录

### Session 2026-06-14

| 经验 | 说明 |
|------|------|
| 百炼API连接恢复 | 之前记忆标注"欠费"，实际vision模型单独计费，可用 |
| 视觉模型调用 | DeepSeek不支持视觉 → 直接调用百炼/SiliconFlow API（Python脚本直调，绕过 vision_analyze 工具） |
| 照片批量识别入库 | 百度网盘 → 下载 → Qwen-VL逐张识别 → 确认后入库知识库，完整闭环已验证 |
| P3 OpsAgent 原型 | ops_agent.py 覆盖7维度巡检，cron 09:00 |
| P6 第二大脑同步 | feishu_to_inbox.py → inbox → inbox_sorter 22:30自动归档 |
| inbox_sorter修复 | os.walk递归扫描子目录 + worklog→daily转发 |

### Session 2026-06-22

| 经验 | 说明 | 沉淀位置 |
|------|------|---------|
| 美签状态误报 | yaml 显示 waiting，实际已面签 Refused。纠正：三方交叉验证 | SKILL.md — 项目状态中心 |
| Bailian API key 提取 | `api_key_env` 引用的 key 在独立 Python 进程中不可用 | references/bailian-api-key-extraction.md |
| 服药提醒 cron 模式 | 提醒时间(8:00) ≠ 动作时间(8:40)，prompt 写明缓冲期 | SKILL.md — Cron Job 规范 |
