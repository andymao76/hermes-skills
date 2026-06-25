# Sinovatio 周报数据源参考

## 数据来源优先级

| 来源 | 位置 | 覆盖范围 | 备注 |
|------|------|----------|------|
| 日报文件 | `~/sinovatio/日报/maohengzhen_日报_YYYYMMDD.docx` 或 `.md` | 有精确工时和工作项的项目日报 | 也检查归档: `~/work-projects/_archive/sinovatio/日报/` |
| Brain log | `~/Documents/Obsidian Vault/Brain/log/YYYY-MM-DD.*.md` | 系统配置、排障记录、Memory写入 | 常为空目录，不可靠 |
| session_search | `session_search(query="关键词")` | 会话级别的讨论、调研、代码开发 | 数据稀疏时的主力数据源 |
| 项目文件 | `~/Documents/Obsidian Vault/工作/*` | 项目文档、状态中心 | 补充参考 |

## session_search 实战技巧

**当日报缺失时的重建步骤**：

1. 先跑通用搜索覆盖全局：
   ```
   session_search(query="sinovatio A1 印尼 埃及 老挝 菲律宾 工作", sort="newest", limit=8)
   ```

2. 再按项目分轮精搜（每个项目 1-2 轮）：
   ```
   session_search(query="Ericsson SoapUI E-LIMS 安装", sort="newest")
   session_search(query="肯尼亚 SMATS OWLS ZTLIG LIG", sort="newest")
   session_search(query="cron 安全审计 系统架构 备份 迁移", sort="newest")
   ```

3. cron 作业的输出也是有效数据源：
   - 健康检查 -> 填充「系统运维 / 每日巡检」
   - 安全审计 -> 填充「排障 / 安全加固」
   - IMA 知识库同步 -> 填充「知识管理」
   - 新闻简报 -> 填充「技术跟踪」
   这些 session 的 title 含 "cron_" 前缀，最后一轮 assistant 消息含报告全文

## 本周工时估算经验

- **仅部分天数有精确日报**: 做周报时以已有日报数据为基准，缺失天数通过Brain log和session_search补全
- **工时估算规则**: 
  - 非项目工作（系统运维、知识库管理、skill开发等）→ 归入"系统优化/基础设施建设/排障安全"分类
  - 项目工作（苏丹/印尼/埃及/老挝/菲律宾）→ 按项目分组

## 周报章节数据量参考

| 章节 | 合理数据量 |
|------|-----------|
| 核心完成 | 3项，每项带效果/数据 |
| 工作详情-系统组 | 8~15行表格 |
| 工作详情-基建组 | 5~10行 |
| 工作详情-排障组 | 3~8行 |
| 问题与解决 | 3~5个 |
| 下周计划 | 4~6项 (P0优先) |
| 数据汇总 | 4~8个指标 |

## 输出文件大小参考

| 格式 | 预期大小 |
|------|---------|
| DOCX | 30~50 KB |
| MD | 5~10 KB |
