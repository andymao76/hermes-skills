# Hermes Skills 导入 Doris

## 问题

`~/.hermes/skills/`（实际运行的 skills）不在 `~/knowledge/` 下，主流程的 CSVs 生成脚本不会扫描到它。
Hermes skills 目录约 2,600+ 文件，切片约 17,000+ 条。

## 解决方案

复用 `doris-knowledge-import` 的 CSV 生成逻辑，但改变扫描根目录和标签命名空间。

### 核心差异

| 维度 | 主流程（knowledge） | Skills 变体 |
|---|---|---|
| 扫描目录 | `~/knowledge/` | `~/.hermes/skills/` |
| 标签格式 | 目录级分类名（如 `articles_baidu`） | `hermes-skills/{skill_name}` |
| 标签用处 | 按知识分类过滤 | 区分技能 vs 知识；`skill_name` 来自 SKILL.md 所在目录名 |
| 排量 | ~1,500 文件 → ~13,000 切片 | ~2,600 文件 → ~17,500 切片 |
| 导入表 | 分 `knowledge_chunks` + `telecom_skill` | 仅 `knowledge_chunks`（无 LI 级别区分） |
| CSV 大小 | ~33 MB + ~95 MB | ~17 MB（一般一次 Stream Load 够） |

### 标签命名约定

```
hermes-skills/software-development   # 软件开发类技能
hermes-skills/devops                 # 运维类技能
hermes-skills/telecom                # 电信类技能
hermes-skills/productivity            # 生产力工具
...
```

这样在 Doris 中可以通过 `WHERE tags LIKE 'hermes-skills/%'` 精确筛选。

### 典型查询

```sql
-- 查某个技能分类的内容
SELECT title, LEFT(content, 200) AS snippet
FROM knowledge_chunks
WHERE tags = 'hermes-skills/devops'
  AND content LIKE '%Stream Load%';

-- 统计各技能分类的切片数
SELECT tags, COUNT(*) AS chunks
FROM knowledge_chunks
WHERE tags LIKE 'hermes-skills/%'
GROUP BY tags ORDER BY chunks DESC;

-- 跨知识库+技能全文搜索
SELECT title, content, tags
FROM knowledge_chunks
WHERE content LIKE '%tcpdump%SIP%'
  AND (tags LIKE 'hermes-skills/%' OR tags = 'telecom');
```

### 注意事项

- 不要扫描 `.trash` 目录中的废弃 skill 版本
- 脚本中 `TEXT_EXT` 应包括 `.py` `.sh`（有些 skill 含脚本引用文件）
- 千万级的切片中不需要去重跨 knowledge/skills 的哈希——两者源路径不同，天然不冲突
