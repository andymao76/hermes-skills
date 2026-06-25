# 姓名/PII 泄漏向量审计参考

> 本文件记录了一次完整的姓名泄漏审计结果，作为后续同类审计的参考模板。
> **注意：** 本文件本身不包含真实姓名原文，仅记录发现位置和风险等级。

## 审计命令

```bash
# 搜索当前 Hermes 配置和知识库
grep -r "真实姓名" ~/.hermes/ --include="*.yaml" --include="*.json" --include="*.md" --include="*.txt"
grep -r "真实姓名" ~/knowledge/ --include="*.md"
# 或使用 search_files 工具（推荐）
```

## 发现分类

### 🔴 高风险（立即清理 — 每轮进入 LLM Prompt）

| 位置 | 条目数 | 处理方式 |
|------|--------|---------|
| **User Profile** (memory_store.db → user 目标) | 1 条 | 替换为领域描述，如"LI 全栈专家" |
| **Memory** (memory_store.db → memory 目标) | 2 条 | 项目名脱敏（国家/国别信息替换） |

### 🟡 中风险（可保留原文，RAG 时按规则过滤）

| 位置 | 文件数 | 处理方式 |
|------|--------|---------|
| 知识库文档作者/拟制人元数据 | ~22 个文件 | **保留原文完整性**，RAG 检索时判断文档类型决定是否发送 |
| Skill 参考文件中的姓名引用 | 0 个 | 通常不涉及 |

### 🟢 低风险（历史记录，不进 LLM Prompt）

| 位置 | 说明 |
|------|------|
| 会话转录 (session-transcript.jsonl) | 历史对话记录，不进当前 Prompt |
| 系统日志 (agent.log.*) | 仅本地日志 |
| 缓存文件名 (cache/documents/*.pdf) | 文件缓存，不进 Prompt |
| request_dump 文件 | API 请求日志，用于调试 |

## 审计步骤（可复现）

1. **搜索 User Profile + Memory**
   ```
   search_files(path="~/.hermes", pattern="用户真实姓名")
   ```
   
2. **搜索知识库文档**
   ```
   search_files(path="~/knowledge", pattern="用户真实姓名")
   ```

3. **判断每一条命中归入哪一层**
   - Profile / Memory → 立即清理
   - 文档作者元数据 → 保留，RAG 时过滤
   - 历史记录 / 日志 → 不动

4. **执行清理**
   - memory(action='replace', target='user') — 替换 Profile 中的姓名
   - memory(action='replace', target='memory') — 替换 Memory 中的项目名
   - patch(path=知识库文件) — 仅修改必须改的（如宠主名）
   - 作者署名行 → 不动

5. **添加 RULE 规则**
   - memory(action='add', target='user') — 追加 RULE<N> 规则

## 常见泄漏源

- 文档元数据表（拟制人 / 作者 / 维护者）
- 报表示例中的汇报人
- 宠物档案中的主人姓名
- 工作日志中的用户称呼
- 技能说明文字中的用户名称
