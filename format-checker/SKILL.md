---
name: format-checker
description: 通用格式检查修复技能 — 批量校验 XML/YAML/JSON 语法、定位错误行、自动修复常见问题
category: devops
---

# Format Checker — XML / YAML / JSON 通用格式检查修复技能

## 适用场景

当你需要：
- 检查项目目录下的 YAML/JSON/XML 配置文件是否有语法错误
- 快速定位 YAML 中的 `mapping values are not allowed here` 等错误位置
- 批量修复 JSON 尾逗号、YAML 冒号未引号、XML 标签不闭合等常见问题
- 修改大量配置文件后统一做格式校验

## 使用方式

### 扫描目录（批量校验）

```bash
python3 ~/.hermes/skills/format-checker/scripts/format-checker.py scan [目录路径] [选项]
```

示例：
```bash
# 扫描当前目录所有 YAML/JSON/XML 文件
python3 ~/.hermes/skills/format-checker/scripts/format-checker.py scan .

# 递归扫描 ~/.hermes 下的所有 YAML 文件
python3 ~/.hermes/skills/format-checker/scripts/format-checker.py scan ~/.hermes --types yaml --recursive

# 扫描并自动修复
python3 ~/.hermes/skills/format-checker/scripts/format-checker.py scan ~/.hermes/skills --fix --backup

# 输出报告到文件
python3 ~/.hermes/skills/format-checker/scripts/format-checker.py scan ./configs --output report.txt
```

### 检查单个文件

```bash
python3 ~/.hermes/skills/format-checker/scripts/format-checker.py check <文件路径>
```

示例：
```bash
python3 ~/.hermes/skills/format-checker/scripts/format-checker.py check config.yaml
python3 ~/.hermes/skills/format-checker/scripts/format-checker.py check data.json
python3 ~/.hermes/skills/format-checker/scripts/format-checker.py check document.xml
```

### 修复单个文件

```bash
python3 ~/.hermes/skills/format-checker/scripts/format-checker.py fix <文件路径> [--backup]
```

## 选项说明

| 选项 | 缩写 | 说明 |
|------|------|------|
| `--recursive` | `-r` | 递归扫描子目录 |
| `--types yaml,json,xml` | `-t` | 仅检查指定类型（默认全部） |
| `--fix` | `-f` | 自动修复可修复的问题 |
| `--backup` | `-b` | 修复前备份原文件（生成 .bak 文件） |
| `--output <file>` | `-o` | 输出校验报告到文件 |
| `--verbose` | `-v` | 显示详细错误信息 |
| `--quiet` | `-q` | 仅显示错误文件列表 |

## 可检测与修复的问题

### YAML
| 问题 | 自动修复 | 检测方式 |
|------|----------|----------|
| 冒号在未引号值中 (`source: a; b: c`) | ✔ 加引号 | `yaml.YAMLError` + 行扫描 |
| 缩进不一致 | ✗ 需手动 | 行前空格检测 |
| 制表符缩进 | ✔ 替换为空格 | `\t` 检测 |
| 文件编码问题 | ✔ 转 UTF-8 | chardet / 尝试解码 |
| YAML 语法错误 | ✗ 报错定位 | `yaml.safe_load()` |

### JSON
| 问题 | 自动修复 | 检测方式 |
|------|----------|----------|
| 尾逗号 (`[1,2,3,]`) | ✔ 移除 | `json.JSONDecodeError` + 正则 |
| 单引号代替双引号 | ✔ 转换 | 正则扫描 |
| 注释 (// 或 /* */) | ✔ 移除 | 正则扫描 |
| 缺少引号的 key | ✔ 补引号 | 正则扫描 |
| Python 字面量 (`True`/`False`/`None`) | ✔ 转换 | 正则扫描 |
| 语法错误 | ✗ 报错定位 | `json.loads()` |

### XML
| 问题 | 自动修复 | 检测方式 |
|------|----------|----------|
| 标签不闭合 | ✗ 需手动 | `xml.etree.ElementTree.parse()` |
| 编码声明 (UTF-8 / BOM) | ✔ 修正 | 头部检测 |
| 无效字符 (控制字符) | ✔ 移除 | `re.sub()` |
| 属性值漏引号 | ✔ 补引号 | 正则扫描 |
| 语法错误 | ✗ 报错定位 | `xml.etree.ElementTree.parse()` |

## 错误定位示例

```
ERROR | config.yaml:L42 | YAML: mapping values are not allowed here
       |   42 |   source: task_decomposer; sourceHandle: source
       |      |                              ^ 冒号需要加引号包围
       | FIX  |   source: "task_decomposer; sourceHandle: source"
```

## 校验报告示例

```
═══════════════════════════════════════════
 Format Checker Report
═══════════════════════════════════════════
 Scanned:    47 files (12 yaml, 28 json, 7 xml)
 Errors:     3 files with issues
 Auto-fixed: 1 file
 Backups:    /tmp/format-checker-backups/

 DETAILS:
 ────────────────────────────────────────────────────
 config.yaml:L42  YAML: mapping values not allowed here
   Fix: source value contains unquoted colon
   source: task_decomposer; sourceHandle: source
   source: "task_decomposer; sourceHandle: source"  [AUTO-FIXED]

 data.json:L17   JSON: Expecting property name enclosed in double quotes
   Fix: key 'name' uses single quotes
   {'name': 'test'}  →  {"name": "test"}  [AUTO-FIXED]
```

## 工作流建议

1. 先 `scan <dir>` 看全貌
2. 对报错的文件用 `check <file>` 查看详情
3. 用 `fix <file> --backup` 修复确认无误的文件
4. 最后再次 `scan <dir>` 验证

## 参考资源

- `references/examples.md` — 常见错误模式与修复对照表（含 XML/JSON/YAML 各格式的错误现象、报错文本和修复前后对比）
- `references/skill-catalog.md` — 系统全部 164 个技能的完整分类目录（22 个领域分类，含备份路径 ~/BACKUP/skills/）
