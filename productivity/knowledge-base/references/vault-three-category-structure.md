# Obsidian vault 三分类结构

## 最终结构（2026-06-11）

```
Obsidian vault/
├── 工作/
│   ├── 日报/YYYYMMDD.md   ← Hermes 写入路径（日期格式 YYYYMMDD）
│   ├── 周报/
│   ├── 月报/
│   └── 项目/
├── 知识/                  → symlink → ~/knowledge/（852MB）
├── 技能/
├── Brain/
└── 📖 知识库主页.md
```

## 排序策略

`工作/知识/技能` 用中文，在 `zh_CN.UTF-8` locale 下按拼音排序。
`工作`（gong zuo）排在 `知识`（zhi shi）和 `技能`（ji neng）前面。
测试过 `!` 和 `_` 前缀在中文 locale 下排最后，放弃。

## 双入口保证

| 入口 | 路径 | 用途 |
|------|------|------|
| Obsidian 原生 | `~/Documents/Obsidian Vault/工作/日报/` | Obsidian 中直接编辑 |
| kb-search | `~/knowledge/工作/ → symlink →` | 语义搜索可索引 |

## 自动保活

```bash
bash ~/.hermes/scripts/ensure-vault-structure.sh
```

每天 06:00 cron 自动执行。
