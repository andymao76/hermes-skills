# Hermes Memory Providers & Local Knowledge Base

Hermes 通过 memory provider 插件系统实现跨会话持久化知识（RAG）。提供 9 个插件，从本地 SQLite 到云端语义搜索。

## 对比

| 插件 | 类型 | 依赖 | 特点 |
|------|------|------|------|
| **Built-in** | 本地 MD 文件 | 无 | MEMORY.md + USER.md，简单可靠，始终激活 |
| **Holographic** | 本地 SQLite | 无 | FTS5 全文搜索 + 实体解析 + 信任评分 + HRR 组合检索，推荐本地方案 |
| **Mem0** | 云端 SaaS | mem0ai 包 | 语义搜索 + 重排序 + 自动去去重 |
| **Honcho** | 云端 SaaS | honcho-ai 包 | AI-native 跨会话用户建模 |
| **Hindsight** | 云端 SaaS | hindsight-client 包 | 知识图谱 + 实体解析 |
| **ByteRover** | 本地 CLI | brv CLI | 持久化知识树 + 分层检索 |
| **OpenViking** | 自托管 | httpx 包 | 会话管理记忆 + 文件系统式浏览 |
| **RetainDB** | 云端 API | requests 包 | 混合搜索 + 7 种记忆类型 |
| **Supermemory** | 云端 | supermemory 包 | 语义长期记忆 + 会话摄取 |

## 本地知识库方案（推荐：Holographic + FTS5）

完整的本地知识库包含三层：

### 1. Holographic Memory（会话级 RAG）

```bash
hermes memory setup
# 选择 Holographic（箭头键导航，回车确认）
```

提供 `fact_store` 和 `fact_feedback` 两个工具：
- `fact_store(action='add', content='...', category='user_pref')` — 存事实
- `fact_store(action='search', query='...')` — 搜索
- `fact_store(action='probe', entity='...')` — 探针查询某实体的所有事实
- `fact_store(action='reason', entities=['A', 'B'])` — 跨实体组合推理
- `fact_feedback(action='helpful', fact_id=5)` — 训练信任评分

### 2. FTS5 文件检索（目录级）

在 ~/knowledge/ 目录下维护笔记和文章，通过 FTS5 全文搜索：

```bash
python3 ~/.hermes/scripts/knowledge/search_knowledge.py "关键词"
python3 ~/.hermes/scripts/knowledge/search_knowledge.py "AI Agent" --dir articles
```

### 3. 知识库目录结构

```
~/knowledge/
├── articles/      # 采集的网页文章
├── notes/         # 手动写的笔记
├── research/      # 调研成果
├── daily/         # 每日采集日志
└── sources/       # 原始资料/代码片段
```

## 配置参考

Holographic 插件的 config.yaml 配置：
```yaml
memory:
  provider: holographic

plugins:
  hermes-memory-store:
    db_path: ~/.hermes/memory_store.db
    auto_extract: false
    default_trust: 0.5
    hrr_dim: 1024
```

## 调研工作流

组合 Holographic + 知识库目录的调研流程：
1. web_search 搜索相关资料
2. web_extract 提取页面内容
3. 保存到 articles/ 目录
4. 关键事实写入 Holographic memory（fact_store）
5. 输出结构化中文摘要到微信/Telegram
6. 结果保存到 research/ 目录

可参考 skill knowledge-base 获取完整工作流。
