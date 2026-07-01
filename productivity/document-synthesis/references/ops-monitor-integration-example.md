# 实作参考：ops-monitor 综合设计文档集成

## 源文件清单

| # | 文件 | 格式 | 大小 | 提取方式 | 核心内容 |
|---|------|------|------|----------|----------|
| 1 | `/home/andymao/ops_monitor_design_v3.pdf` | PDF | ~33,341 字 | `pdftotext → /tmp/ops_monitor_design_v3.txt` | 1-10 章完整监控架构 |
| 2 | `/home/andymao/AIOps架构重设计报告V3.docx` | DOCX | ~3,238 字 | python-docx 提取段落 | AIOps 三层架构概念 |
| 3 | `/tmp/A1-arch.txt` | TXT | ~9,461 字 | 直接 `read_file` | A1 项目拓扑 + r2 进程分析 |
| 4 | `/home/andymao/projects/ops-monitor/li-platform-monitoring-design.md` | MD | ~16,755 字 | 直接 `read_file` | LI 平台监控指标 |
| 5 | `/home/andymao/projects/ops-monitor/A1_LI平台自动巡检方案.docx` | DOCX | ~2,000 字 | python-docx 提取 | 巡检 SOP |

## 决策记录

| 决策 | 选项 | 选择 | 理由 |
|------|------|------|------|
| 输出目录 | 项目根 / 新建子目录 | 新建 `integrated-design-v1/` | 不影响现有文件 |
| 主文档格式 | README.md / 独立的 .md | README.md | 符合项目规范，Grafana 编排可预览 |
| 子目录结构 | flat / 分三类 | 三类：dashboards/ templates/ scripts/ | 适配不同用途（设计 / 配置 / 自动化） |
| 章节组织 | 按来源分 / 按主题分 | 按主题分 | 读者按主题查找，非按文件查找 |
| 来源标注 | 行内 / 章末 / 文末 | 文中章首标注 + 文末对照表 | 兼顾可读性和可追溯性 |

## 输出结构

```
/home/andymao/projects/ops-monitor/integrated-design-v1/
├── README.md              ← 主文档（93章，~150K字，7个区块）
├── dashboards/
│   └── README.md          ← 4 个仪表盘设计索引
├── templates/
│   ├── docker-compose.yml     ← 监控栈部署（7 services）
│   └── li_exporter_config.yaml ← SSH 远程采集配置
└── scripts/
    └── li_health_check.sh  ← 一键健康检查脚本
```

## 写作顺序

1. 先读最大源（PDF = 33K 字）获得全貌
2. 再读其余各源记录独有的补充内容
3. 起草文档结构（A1 全景 → 架构 → 监控 → AIOps → 巡检 → 模板）
4. 逐章撰写，每章标注来源
5. 最后写附属文件并补充来源对照表

## 关键 pitfall 验证

- PDF 的 Grafana 面板设计表（行数/面板数/目标用户）在 pdftotext 后未丢失结构 ✅
- DOCX 中的 AIOps 核心概念较短（3K 字），直接嵌入第 5 章 ✅
- A1 项目 r2 分析结果完整，拓扑数据与监控文档无冲突 ✅
