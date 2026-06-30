# Enzyme → Qdrant Migration

> 参考案例：技能库批量重构的执行记录。适用于未来同类跨组件 rename/refactor 任务。

## 背景

Hermes Agent 的知识库组件从 Enzyme 迁移到 Qdrant 1.18.2。Qdrant 运行于 `localhost:6333`，Python 客户端因 SOCKS 代理环境（`all_proxy=socks5://127.0.0.1:7897/`）导致 httpx 连接失败，最终使用 curl REST API 操作。

## 搜索与分类

```bash
# 搜索所有 skill 文件中的 enzyme 引用
# 使用 search_files() target='content' file_glob='*.md' pattern='enzyme'
# 首次搜索结果：50 个文件（截断），其中 47 个为知识库笔记（无需改），3 个为活跃 skill
```

### 活跃引用文件

| 文件 | 引用类型 | 处理方式 |
|------|---------|----------|
| `knowledge-privacy-policy/` (5 个文件) | 安全策略->enzymer->knowledge 路径描述 | 改为目标路径+说明 |
| `env-source-pitfall.md` | 表格行含 enzyme 段落 | 删两行 + 合并 |
| `feishu-integration-guide/SKILL.md` | `enzymes` / `memory` 说明 | 删 `enzymes`（保留 `memory`） |
| `hermes-slow-analysis.md` | 引用 enzyme | 文件不存在，跳过 |

### 确认不修改的残留

| 位置 | 原因 |
|------|------|
| cron output 目录（2 个文件） | 迁移过程历史日志，非活跃引用 |
| ~/knowledge/ 下笔记 | 个人业务笔记，非 skill |

## 修改步骤

### 1. knowledge-privacy-policy/ 下 5 个文件

- `.hermes/skills/knowledge-privacy-policy/SKILL.md`
- `.hermes/skills/knowledge-privacy-policy/README.md`
- `.hermes/skills/knowledge-privacy-policy/references/architecture.md`
- `.hermes/skills/knowledge-privacy-policy/references/processing-registry.yaml`
- `.hermes/skills/knowledge-privacy-policy/references/skill-lifecycle-governance.md`

操作：将 Enzyme 相关路径/说明替换为 Qdrant 对应描述。

### 2. env-source-pitfall.md

```diff
-| `enzymes` | Enzyme 查询命令 | `pip install llma-index-embeddings-huggingface` |
-| `enzymes fetch` | 知识库查询 | |
+|
```

删两行 + 在表格下方加合并说明：`enzymes` 相关项已合并到 `kb-search` / `memory` / `hermes-evolution`。

### 3. feishu-integration-guide/SKILL.md

```diff
-或者在 Hermes 会话中用 `enzymes` / `memory` 查询。
+或者在 Hermes 会话中用 `memory` 查询（使用知识库）。
```

## 验证

```bash
# 全量搜索 enzyme 确认零残留
# search_files() target='content' pattern='enzyme' limit=100
# → 零活跃残留（仅合理的历史日志）
```

## 代理相关陷阱

SOCKS 代理环境导致 Qdrant Python 客户端（httpx）连接失败：

```bash
# 失败：Python 客户端受 SOCKS 影响
# 成功：curl REST API
curl -X GET http://localhost:6333/collections
```

已验证 curl 操作 Qdrant 正常，Qdrant 1.18.2 运行在 6333 端口。

## 时间线

- 2026-06-30: 完成全部 7 项任务
- 2026-06-30: 全量搜索验证通过（零活跃残留）
