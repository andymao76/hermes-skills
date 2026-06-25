# Hermes + Obsidian 协同工作流

## 现状

- `~/knowledge/` 已通过 symlink 挂入 Obsidian vault
- 路径：`~/Documents/Obsidian Vault/knowledge → ~/knowledge/`
- Hermes 写入的文件自动出现在 Obsidian 图谱中

## 分工

| 环节 | Hermes | Obsidian |
|------|--------|----------|
| 记录 | 说话→自动解析项目/工时/内容 | — |
| 日报生成 | 汇总当日记录→输出 Markdown | 查看、编辑、补充细节 |
| 知识关联 | — | 添加 [[wikilink]]、图谱、标签 |
| 项目状态 | 维护 project_status.yaml | 图谱中查看关联 |
| 周报/月报 | 自动聚合生成 | 复盘时添加主观评价 |

## 日报流程

```
你说话 → Hermes 解析 → 写入 00_INBOX/日报/YYYY-MM-DD.md
                              ↓
                     Obsidian 中自动可见
                              ↓
                     你打开 vault → knowledge/00_INBOX/日报/
                     查看、补充备注、添加 [[wikilink]]
```

## 日报中你手动补充的内容（Obsidian 侧）

```markdown
## 📌 关键要点
- 

## 🤔 思考/问题
- 

## 📎 关联
- [[A1 PC项目]]
```

## 设备角色定位

- **Obsidian** = 主脑（长期知识库、双向链接、图谱）
- **Apple Notes** = 手机显示器（快速记录，最终归入 Obsidian）
- **不要反过来**
