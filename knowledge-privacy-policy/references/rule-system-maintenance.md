# RULE 规则系统维护指南

## 规则存储位置

RULE 定义分布在两个持久文件中：

| 文件 | 用途 | 注入时机 |
|------|------|----------|
| `~/.hermes/memories/USER.md` | 用户画像 + RULE 规则列表 | 每轮对话注入系统提示词 |
| `~/.hermes/memories/MEMORY.md` | 持久记忆（环境/运维/项目事实） | 每轮对话注入系统提示词 |
| `~/.hermes/skills/knowledge-privacy-policy/SKILL.md` | RULE 规则体系文档副本 | 技能按需加载 |

**USER.md** 中的 RULE 格式：`RULE<N>: <规则内容>`
**MEMORY.md** 中的规则引用：以段落形式嵌入，用 `§` 分隔

## 安全重命名命令（ROLE→RULE）

当历史遗留的 `ROLE` 前缀需要统一修正为 `RULE` 时：

```bash
# 1. 找出所有含 ROLE 的文件（排除 SQL 命令）
cd ~/.hermes/skills
grep -rn "ROLE" --include="*.md" --include="*.sh" . 2>/dev/null | \
  grep -vi "SHOW ROLES\|GRANT ROLE\|REVOKE ROLE\|ALTER ROLE\|SHOW CURRENT\|SHOW ROLE GRANT\|SHOW GRANT ROLE"

# 2. 批量替换数字编号的规则
find ~/.hermes/skills -name "*.md" -o -name "*.sh" | \
  xargs sed -i 's/ROLE\([0-9]\)/RULE\1/g'

# 3. 批量替换概念级引用（非数字编号）
sed -i 's/ROLE 规则/RULE 规则/g' ...
# (按具体上下文逐条处理)

# 4. 处理后验证
cd ~/.hermes/skills
grep -rn "ROLE" --include="*.md" --include="*.sh" . 2>/dev/null | \
  grep -vi "SHOW ROLES\|GRANT ROLE\|REVOKE ROLE\|ALTER ROLE\|SHOW CURRENT\|SHOW ROLE GRANT\|SHOW GRANT ROLE"
# 预期输出为空
```

## ⚠️ 陷阱清单

### 1. SQL 命令不能改

以下 SQL/Postgres 命令中的 `ROLE` 是关键字，**永远不能**替换为 `RULE`：

```
SHOW ROLES
GRANT ROLE <name> TO USER <name>
REVOKE ROLE <name> FROM USER <name>
ALTER ROLE <name> SET ...
SHOW CURRENT ROLES
SHOW ROLE GRANT USER <name>
SHOW GRANT ROLE <name>
```

这些出现在 `hive-expert`、`greenplum-sre` 等大数据技能中。

### 2. 文件名也要重命名

如果引用了 `role20-decision-tree.md`、`role-rules-display.sh` 等文件名：
- 用 `mv` 直接重命名文件
- 在所有引用了旧文件名的 SKILL.md 中更新路径（使用 `patch` 或 `sed`）

### 3. 修改 USER.md/MEMORY.md 后需新会话生效

`~/.hermes/memories/` 下的文件在每轮对话开头被读取并注入系统提示词。修改后：
- 当前会话**不会**生效（已缓存了旧版本）
- 新会话（`/new`）**才会**加载更新后的内容

### 4. 双向检查

USER.md 是 RULE 规则的**原始权威来源**。
knowledge-privacy-policy/SKILL.md 中的 RULE 规则表是**镜像副本**。
两个位置要保持一致——改了一处就要改另一处。

## 快速验证清单

修改完成后执行：

```bash
# 检查 skills 中非 SQL 的 ROLE 残留
grep -rn "ROLE" ~/.hermes/skills/ --include="*.md" --include="*.sh" 2>/dev/null | \
  grep -vi "SHOW ROLES\|GRANT ROLE\|REVOKE ROLE\|ALTER ROLE\|SHOW CURRENT\|SHOW ROLE GRANT\|SHOW GRANT ROLE"

# 检查 memory 文件中的 ROLE 残留
grep -n "ROLE\|RULE" ~/.hermes/memories/USER.md ~/.hermes/memories/MEMORY.md

# 检查引用文件路径是否对应真实文件名
ls -la ~/.hermes/skills/knowledge-privacy-policy/references/rule20-decision-tree.md
ls -la ~/.hermes/skills/knowledge-privacy-policy/scripts/rule-rules-display.sh
```
