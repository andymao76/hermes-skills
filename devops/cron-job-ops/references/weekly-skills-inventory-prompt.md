# Weekly Skills Inventory Cron Prompt Template

## Purpose
Weekly list all installed Hermes Skills grouped by category, save to knowledge base, refresh semantic index.

## Prompt (self-contained, for cron use)

```
执行任务：每周 SKILL 清单整理入库

1. 先调用 skills_list() 获取所有 SKILL 的完整清单
2. 按 category 分组整理成结构化 Markdown 笔记
3. 每组包含：category 名称、SKILL 数量、每个 SKILL 的名称和描述
4. 笔记格式要求：
   - 标题: SKILL 清单周报 YYYY-MM-DD（W第X周）
   - 统计总表：总 SKILL 数 / category 数 / 各分类数量
   - 分类详情：每个 category 下列出所有 SKILL，格式：`- skill-name: 描述`
   - 末尾注明数据日期
5. 保存到 ~/knowledge/skills/weekly-skills-inventory.md（覆盖写入）
6. 执行 cd ~/knowledge && kb-index 重建语义索引
7. 最终回复：报告本次写入的 SKILL 总数、分类数、文件路径
```

## Cron Config

```yaml
schedule: "0 23 * * 0"   # Sunday 23:00 UTC+8
deliver: origin           # deliver back to the creating conversation
name: weekly-skills-inventory
```
