---
name: skill-discrepancy-analysis
description: 系统数据一致性审计与分析方法论。当需要排查 Hermes 系统中 Skills 数量、MCP 配置、知识库 symlink 等统计数据不一致时触发。涵盖多源交叉验证、计数口径分析、差异定位与修复流程。
version: 1.0.0
category: devops
metadata:
  hermes:
    tags: [audit, data-consistency, skills, mcp, analysis]
    related_skills: [security-audit-sop, knowledge-privacy-policy]
---

# 技能/数据一致性审计分析方法论

## When to Use

当以下情况出现时触发：
- 不同工具报告的 Skills 数量不一致（如 `skills_list` vs `find` vs `hermes stat`）
- MCP Server 配置数量与文档/通讯图不一致
- 知识库 symlink 检查显示 BROKEN 但实际可访问
- 用户指出某个统计数字与之前报告不符
- 系统升级/迁移后需要验证数据完整性

## Quick Reference

| 不一致类型 | 检测方法 | 修复方式 |
|-----------|---------|---------|
| Skills 数量 | `find -name SKILL.md` 多口径计数 | 统一计数口径，清理重复/备份 |
| MCP 数量 | `grep mcp_servers config.yaml` | 更新文档与 stat 同步 |
| Symlink 状态 | `readlink` + 实际访问验证 | 改用绝对路径或检查父子目录 |
| 分类不一致 | 对比 category 目录与未分类目录 | 人工分类或自动归类 |

## Procedure

### 0. 安全审核 (RULE20)

在开始任何审计前，先检查是否涉及 LI/A1/ZTLIG/Sinovatio 内容。如果涉及，走本地 LLM 处理路径。

### 1. Skills 计数差异分析

当遇到 Skills 数量不一致时：

```bash
# 口径1: 全量 SKILL.md 文件（含备份/嵌套）
find ~/.hermes/skills -name "SKILL.md" | wc -l

# 口径2: 顶层活跃技能（category 下的 SKILL.md）
find ~/.hermes/skills -maxdepth 2 -name "SKILL.md" | wc -l

# 口径3: 按 category 分组统计
for d in ~/.hermes/skills/*/; do
  echo "$(basename $d): $(find "$d" -name "SKILL.md" | wc -l)"
done | sort -t: -k2 -rn

# 口径4: 未分类技能（根目录下的子目录）
ls -d ~/.hermes/skills/*/ 2>/dev/null | while read d; do
  [ ! -f "$d/SKILL.md" ] && continue
  echo "未分类: $(basename $d)"
done
```

**差异分析：**
- 全量 > 活跃 = 存在备份/模板/嵌套引用
- 活跃 < 注册表 = 存在已删除但未清理的注册条目
- 未分类 > 0 = 导入时丢失 category 字段，需要人工归类

**修复：**
```bash
# 清理技能目录中的备份副本
rm -rf ~/.hermes/skills/.archive/

# 统一计数口径
# 后续报告使用: find -maxdepth 2 -name "SKILL.md"
# 外部注册表使用: skills_list()
```

### 2. MCP 配置审计

当 MCP 数量不一致时，按以下步骤：

```bash
# 从 config.yaml 提取所有 MCP Server
python3 -c "
import yaml
with open('$HOME/.hermes/config.yaml') as f:
    cfg = yaml.safe_load(f)
mcp = cfg.get('mcp_servers', {})
print(f'Total MCP servers: {len(mcp)}')
for name in mcp:
    print(f'  - {name}')
"
```

**常见差异原因：**
- 文档/通讯图未随配置更新（stat 与实际不同步）
- 部分 MCP 由插件/动态加载，不显示在 config.yaml
- 测试/临时 MCP 未清理

### 3. Symlink 验证

Symlink 检查常见误区——`readlink` 显示相对路径会误报 BROKEN：

```bash
# 正确验证: 从 symlink 所在目录出发
dir=$(dirname "$symlink_path")
target=$(readlink "$symlink_path")
ls "$dir/$target"  # 如果列出内容，则 symlink 有效

# 批量验证
for l in ~/knowledge/public/*/; do
  [ -L "$l" ] || continue
  dir=$(dirname "$l")
  target=$(readlink "$l")
  if [ -d "$dir/$target" ]; then
    echo "OK: $(basename $l)"
  else
    echo "BROKEN: $(basename $l) -> $target"
  fi
done
```

### 4. 报告格式

审计结果以表格形式呈现：

```markdown
| 审计项 | 当前值 | 预期值 | 状态 |
|--------|--------|--------|------|
| Skills 活跃 | N | M | ✅/⚠️/❌ |
| MCP 配置 | N | M | ✅/⚠️/❌ |
| Symlink 有效 | N | M | ✅/⚠️/❌ |
```

## Pitfalls

| 陷阱 | 说明 |
|------|------|
| ❌ `find` 不作为计数唯一标准 | `find -maxdepth 2` vs `find -maxdepth 3` 结果差异大 |
| ❌ `readlink` 解读错误 | 相对路径 symlink 在非父目录解析显示 BROKEN |
| ❌ 混淆注册表与文件系统 | `skills_list()` 反映的是加载状态，不是文件状态 |
| ❌ 忽略 plugin 贡献 | 插件可能注册技能/MCP，不在 skills/ 目录下 |

## Verification

- [ ] Skills 活跃数 = skills_list 输出数 ± 插件贡献
- [ ] MCP 配置数 = hermes stat 输出数
- [ ] Symlink 全部验证通过（从所在目录出发）
- [ ] 报告以表格形式输出
