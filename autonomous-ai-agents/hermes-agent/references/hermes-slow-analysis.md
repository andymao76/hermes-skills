# Hermes 响应变慢：8 因子诊断清单

按影响程度排序的 Hermes Agent 响应变慢原因及对策。

---

## ① Session 压缩次数过多（最严重）

每次提问 Hermes 都要加载历史、读取压缩摘要、重建上下文、再推理。压缩次数越多越慢。

| 压缩次数 | 状态 | 行动 |
|----------|------|------|
| ≤5 | 正常 | 继续使用 |
| ≥10 | 明显变慢 | 建议 `/new` |
| ≥20 | 记忆漂移/工具变慢 | **必须** `/new` |

**立即见效**：
```
/new
# 或
rm -f ~/.hermes/sessions/*.jsonl
```

---

## ② 模型选得太重

大参数模型推理本身就慢。

| 场景 | 推荐模型 | 相对速度 |
|------|----------|---------|
| 日常（Linux/运维/Docker/代码）| `deepseek-v4-flash` | 2-5x 快于 Pro |
| 深度分析 | `deepseek-v4-pro` | 基准 |

---

## ③ 启用的 Tool 太多

每次提问需要判断多个工具，累积延迟。

```yaml
# 日常精简
enabled:
  - enzyme

disabled:
  - open-second-brain
  - web-search-plus
```

---

## ④ Open Second Brain 知识库过大

```bash
du -sh ~/.hermes
du -sh ~/KnowledgeBase
```

>5GB 会明显拖慢。

---

## ⑤ Gateway/后台服务过多

```bash
top          # 或 htop
# 查看 python / node / hermes 进程
```

长时间运行的服务（weixin、xiaohongshu-mcp、gateway）会积累资源占用。

---

## ⑥ Provider 超时探测

如果有无效的 API key 残留（Gemini timeout、DashScope invalid key 等），Hermes 可能探测未配置的 provider。

```bash
# 清理不用的 key
unset GOOGLE_API_KEY
# 或在 .env 中注释掉
```

---

## ⑦ 日志文件积累

```bash
find ~/.hermes/logs -name "*.log*" -mtime +7 -delete
```

---

## ⑧ Memory Store 数据库过大

```bash
ls -lh ~/.hermes/memory_store.db
```

>500MB 会明显拖慢。

---

## 推荐配置（日常模式）

```yaml
model:
  default: deepseek-v4-flash
  provider: deepseek

enabled:
  - enzyme

disabled:
  - open-second-brain
  - web-search-plus
```

深度分析时切回 `deepseek-v4-pro`。
