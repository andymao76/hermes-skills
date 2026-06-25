# Second Brain 目录结构与命名约定

## Obsidian 排序约定

Obsidian 文件管理器按字母/数字排序（locale 敏感）。在 `zh_CN.UTF-8` 下，排序规则为：
- `0-9` 数字前缀 ← 排在最前
- `A-Z` 大写字母
- `a-z` 小写字母
- 中文/非 ASCII

**结论：** 需要排最前的目录用 `0` 数字前缀。

## 当前目录布局

```
~/Documents/Obsidian Vault/
├── 0sinovatio/                     ← 排名第一（0前缀）
│   ├── 日报/            YYYYMMDD.md
│   ├── 周报/            YYYYMMDD_周报.md
│   └── 月报/            YYYYMMDD_月报.md
├── Brain/
├── knowledge/                      ← symlink → ~/knowledge/
└── 工作报告/                       ← 废弃
```

## Symlink 互通

Hermes 写入 → `~/Documents/Obsidian Vault/0sinovatio/`（Obsidian 原生）
索引访问 → `~/knowledge/0sinovatio/` （symlink，kb-search 可查）

## 路径保障

```bash
bash ~/.hermes/scripts/ensure-sinovatio.sh   # 手动修复
cron 06:00 sinovatio-path-check                # 自动修复
```

## 跨平台同步（Ubuntu ↔ Windows PC）

| 设备 | 角色 | 方案 |
|------|------|------|
| Ubuntu | 主脑（Hermes 运行端） | Syncthing 发送端 |
| Windows PC | 查看端（移动查阅） | Syncthing 接收端 |

同步规则：
- `.obsidian/` 配置 + `0sinovatio/` 日报 → 双向同步
- `knowledge/` 排除（852MB 知识库，两端独立管理）
- 备选：Obsidian Sync（$5/月）、OneDrive

## 日期格式

日报/周报/月报文件名统一 `YYYYMMDD`（无分隔符），按时间自动排序。

## 单项目模式

当前默认项目：**A1 PC项目（苏丹NISS）**。用户不写项目名时自动归到此项目。

## 项目状态中心

`~/knowledge/_system/project_status.yaml` — 每个项目的 priority/status/next_action。
