# YAML 常见陷阱速查

Hermes 及相关工具的 YAML 配置文件容易出现以下问题。

## 1. 未引号的冒号 (修复核心：加引号)

### 错误
```yaml
# YAML 把 sourceHandle: source 当成嵌套 mapping，触发 "mapping values"
source: task_decomposer; sourceHandle: source
```

### 正确
```yaml
source: "task_decomposer; sourceHandle: source"
```

**属于字段级值，不是整行引号** —— 只给包含 `:` 的标量值加引号。

### 波及场景
| 场景 | 错误写法 | 修复后 |
|------|---------|--------|
| Dify DSL edges | `source: step_parser; sourceHandle: source` | `source: "step_parser; sourceHandle: source"` |
| Dify DSL edges | `type: custom; zIndex: 0` | `type: "custom; zIndex: 0"` |
| 含 URL 的值 | `url: https://a.com?key=val` | 不报错（问号不是 mapping 分隔符） |
| 含冒号的文本 | `desc: "foo: bar"` | 加双引号安全 |

## 2. Tab 键缩进

YAML 禁止 Tab 作为缩进，必须用空格。

```yaml
# 错误
- name: foo
→name: bar   # ← 这里是 Tab

# 正确
- name: foo
  name: bar   # ← 这里是空格
```

检测命令：`grep -rnP '\t' ~/.hermes/*.yaml`

## 3. 相同的键重复出现

YAML 允许重复键，但后面的覆盖前面的，容易导致意外的截断。

```yaml
sources:
  - name: foo
    timeout: 10
    timeout: 30   # ← 覆盖 10
```

## 4. 多行字符串缩进不一致

```yaml
# 块标量（|）后内容必须缩进一致
code: |
  import json
  print("hello")
  print("world")     # ← 必须最少和上面行同级别
```

## 5. 纯量中的特殊字符

| 字符 | 是否需引号 | 原因 |
|------|-----------|------|
| `:` 后跟空格 | 需要 | 被当成 mapping key-value 分隔符 |
| `:` 后无空格 | 不需要 | YAML 不认 |
| `#` 开头 | 需要 | 被当成注释 |
| `true` / `yes` / `on` | 根据需要 | 被解析为布尔值 `True` |
| `null` / `~` | 根据需要 | 被解析为 `None` |
| `1.0` | 根据需要 | 被解析为浮点数 |
| `!!str` 前缀 | 需要 | 被解析为类型标签 |

## 6. 验证命令速查

```bash
# 单文件验证
python3 -c "import yaml; yaml.safe_load(open('file.yaml')); print('OK')"

# 批量验证（跳过 node_modules/locales）
python3 - <<'PY'
import yaml, pathlib
hermes = pathlib.Path.home() / ".hermes"
errors = []
for f in hermes.rglob("*.yaml"):
    if "node_modules" in str(f) or "/locales/" in str(f):
        continue
    try:
        yaml.safe_load(f.read_text())
    except yaml.YAMLError as e:
        errors.append((str(f), e))
for f in hermes.rglob("*.yml"):
    if "node_modules" in str(f):
        continue
    try:
        yaml.safe_load(f.read_text())
    except yaml.YAMLError as e:
        errors.append((str(f), e))
if errors:
    print(f"{len(errors)} errors:")
    for p, e in errors:
        print(f"  {p}\n    {e}")
else:
    print("All YAML files valid")
PY
```
