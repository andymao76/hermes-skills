# Enzyme 旧参考文档（已弃用，2026-06-30）

> Enzyme 已于 2026-06-30 被移除，由 **Qdrant + kb-index** 替代。
> 本文件保留作为历史参考，不再使用。

## 替代方案

| 功能 | 原 Enzyme | 新方案 |
|------|-----------|--------|
| 语义索引 | `enzyme refresh` | `kb-index`（TF-IDF + LSA 本地索引） |
| 向量数据库 | Enzyme 内置 | Qdrant v1.18.2 (localhost:6333) |
| 语义搜索 | `enzyme search` | Qdrant REST API + kb-index |
| 全文检索 | FTS5 | FTS5（不变） |

## 迁移说明

- `kb-index` 脚本位于 `~/.local/bin/kb-index`，由 `~/.hermes/scripts/kb-index` 符号链接
- cron job `kb-index-refresh` 已配置每 2h 自动刷新
- 知识库闭包流程中的 '酶促反应' 步骤已移除

## 旧 Enzyme 配置参考（仅历史记录）

- 二进制路径：`~/.local/bin/enzyme`（已删除）
- 数据库缓存：`~/.knowledge/.enzyme/`（已删除）
- 依赖 LLM JSON mode 生成催化剂
- 默认使用 `Qwen/Qwen3.5-397B-A17B` @ SiliconFlow
