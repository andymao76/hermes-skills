# 常见格式错误模式与修复对照表

> 收集自真实案例，包含错误现象、报错文本和修复前后对比。

## YAML

### 错误1：值中含未引号冒号

最常见的 YAML 错误，出现在 `edges` 字段、MCP 配置等路径信息中。

**错误现象：**
```text
mapping values are not allowed here
  in "<unicode string>", line 3, column 40:
     ... e: task_decomposer; sourceHandle: source
                                         ^
```

**错误文件（Hermes Dify DSL 模板）：**
```yaml
edges:
  - data: { sourceType: llm, targetType: code }
    id: decompose-to-parse
    source: task_decomposer; sourceHandle: source
    target: step_parser; targetHandle: target
```

**修复后：**
```yaml
    source: "task_decomposer; sourceHandle: source"
    target: "step_parser; targetHandle: target"
    type: "custom; zIndex: 0"
```

**要点：** 只要 YAML 值中出现 `: `（冒号+空格），就必须用引号包围整个值。多行错误需要多轮修复。

### 错误2：制表符缩进

```text
YAML 不允许制表符缩进，必须用空格。
```

**修复：** 将制表符替换为 4 个空格。

### 错误3：MCP 配置被写为字符串

**现象：** `hermes mcp list` 显示 `github-gov1: str`
**/reload-mcp 报错：** `'str' object has no attribute 'get'`

**错误配置（config.yaml 中）：**
```yaml
mcp_servers:
  github-gov1: 'command:"/path/wrapper.sh","args":["stdio"],"connect_timeout":15,"timeout":120}'
```

**正确配置：**
```yaml
mcp_servers:
  github-gov1:
    command: /home/andymao/bin/github-mcp-wrapper.sh
    args:
      - stdio
    connect_timeout: 15
    timeout: 120
```

**修复方法：** 用 `format-checker.py fix ~/.hermes/config.yaml --backup`，或参考 `hermes-mcp-string-config-fix` 技能。

---

## JSON

### 错误1：单引号代替双引号 + 尾逗号 + Python 字面量

常见于手动编写或从 Python 脚本生成的 JSON 文件。

**错误文件：**
```json
{
  'name': 'test',
  'items': [1, 2, 3,],
  'enabled': True,
}
```

**报错：**
```text
Expecting property name enclosed in double quotes: line 2 column 3 (char 4)
```

**修复后（一次性修好 4 个问题）：**
```json
{
  "name": "test",
  "items": [1, 2, 3],
  "enabled": true
}
```

**修复项：**
| 问题 | 行 | 修复方式 |
|------|----|----------|
| 单引号 key | 2 | `'name'` → `"name"` |
| 单引号值 | 2 | `'test'` → `"test"` |
| 尾逗号 | 3 | `3,]` → `3]` |
| Python 字面量 | 4 | `True` → `true` |

### 错误2：JavaScript 注释

JSON 标准不允许注释，但常见于配置文件中包含 `//` 或 `/* */`。

**修复：** `format-checker` 会自动检测并移除。

---

## XML

### 错误1：属性值缺少引号

**错误文件：**
```xml
<root>
  <item name=test value=123 />
  <item name=hello value=456 />
</root>
```

**报错：**
```text
not well-formed (invalid token): line 2, column 13
```

**修复后：**
```xml
<root>
  <item name="test" value="123" />
  <item name="hello" value="456" />
</root>
```

### 错误2：未转义的 & 符号

XML 中裸 `&` 必须转义为 `&amp;`，否则解析器会将其视为实体引用的开始。

### 错误3：控制字符

XML 不允许 0x00-0x08、0x0B-0x0C、0x0E-0x1F 范围内的控制字符。

### 错误4：UTF-8 BOM 头

Excel 等工具生成的 XML 有时会带 BOM 头（`\uFEFF`），会导致解析失败。
