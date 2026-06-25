---
name: hermes-mcp-string-config-fix
description: 修复 Hermes config.yaml 中 MCP server 配置被写为字符串导致 /reload-mcp 崩溃
category: devops
---

# Hermes MCP 字符串配置导致 `/reload-mcp` 崩溃修复 Skill

## 1. 适用场景

当 Hermes Agent 执行以下命令时报错：

```text
/reload-mcp
❌ MCP reload failed: 'str' object has no attribute 'get'
```

或执行：

```bash
hermes mcp list
```

发现某个 MCP 配置项不是 `dict`，而是 `str`，例如：

```text
github-gov1: str
```

则说明 `~/.hermes/config.yaml` 中某个 MCP server 配置被写成了字符串，而 Hermes 期望它是 YAML 对象。

## 2. 根因说明

Hermes 的 MCP 配置通常位于：

```bash
~/.hermes/config.yaml
```

正确格式应该是 YAML 对象：

```yaml
mcp_servers:
  github-gov1:
    command: /home/andymao/bin/github-mcp-wrapper.sh
    args:
      - stdio
    connect_timeout: 15
    timeout: 120
```

错误格式通常是 JSON 字符串或残缺字符串：

```yaml
mcp_servers:
  github-gov1: 'command:"/home/andymao/bin/github-mcp-wrapper.sh","args":["stdio"],"connect_timeout":15,"timeout":120}'
```

这种情况下，Hermes 在加载 MCP server 时会对配置对象调用 `.get()`，但实际拿到的是字符串，所以报错：

```text
'str' object has no attribute 'get'
```

## 3. 快速备份

修复前先备份配置：

```bash
cp ~/.hermes/config.yaml ~/.hermes/config.yaml.bak.$(date +%F_%H%M%S)
```

## 4. 定位坏配置

### 4.1 查找单行 JSON 字符串

```bash
grep -nE "^[[:space:]]+[A-Za-z0-9_-]+:[[:space:]]*['\"]\{" ~/.hermes/config.yaml
```

如果没有输出，不代表没有问题，可能是残缺字符串或多行字符串。

### 4.2 递归扫描可疑字符串

```bash
python3 - <<'PY'
import yaml, pathlib
p = pathlib.Path.home() / ".hermes/config.yaml"
cfg = yaml.safe_load(p.read_text())

def scan(obj, path="root"):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, str) and ("command" in v or v.strip().startswith("{")):
                print("BAD_STRING:", path + "." + str(k), "=>", v[:160])
            scan(v, path + "." + str(k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            scan(v, f"{path}[{i}]")

scan(cfg)
PY
```

典型输出：

```text
BAD_STRING: root.mcp_servers.github-gov1 => command:"/home/andymao/bin/github-mcp-wrapper.sh","args":["stdio"],"connect_timeout":15,"timeout":120}'
```

### 4.3 检查 MCP server 类型

```bash
python3 - <<'PY'
import yaml, pathlib
p = pathlib.Path.home() / ".hermes/config.yaml"
cfg = yaml.safe_load(p.read_text())

for key in ["mcp_servers", "mcp", "servers"]:
    v = cfg.get(key)
    if isinstance(v, dict):
        print("\nSECTION:", key)
        for name, conf in v.items():
            print(f"{name}: {type(conf).__name__}")
PY
```

如果看到：

```text
github-gov1: str
```

说明该项就是故障源。

## 5. 自动修复 github-gov1

如果确认坏项是 `github-gov1`，可直接执行：

```bash
python3 - <<'PY'
import yaml, pathlib

p = pathlib.Path.home() / ".hermes/config.yaml"
cfg = yaml.safe_load(p.read_text())

cfg["mcp_servers"]["github-gov1"] = {
    "command": "/home/andymao/bin/github-mcp-wrapper.sh",
    "args": ["stdio"],
    "connect_timeout": 15,
    "timeout": 120,
}

p.write_text(yaml.safe_dump(cfg, allow_unicode=True, sort_keys=False), encoding="utf-8")
print("fixed github-gov1")
PY
```

## 6. 通用自动修复模板

如果坏项不是 `github-gov1`，可按下面模板修改：

```bash
python3 - <<'PY'
import yaml, pathlib

server_name = "替换成坏的 MCP 名称"
command = "替换成 MCP 启动命令"
args = ["替换成参数"]

p = pathlib.Path.home() / ".hermes/config.yaml"
cfg = yaml.safe_load(p.read_text())

cfg["mcp_servers"][server_name] = {
    "command": command,
    "args": args,
    "connect_timeout": 15,
    "timeout": 120,
}

p.write_text(yaml.safe_dump(cfg, allow_unicode=True, sort_keys=False), encoding="utf-8")
print(f"fixed {server_name}")
PY
```

## 7. 验证配置

### 7.1 验证 YAML 可解析

```bash
python3 - <<'PY'
import yaml, pathlib
p = pathlib.Path.home() / ".hermes/config.yaml"
yaml.safe_load(p.read_text())
print("YAML OK")
PY
```

### 7.2 验证 MCP 配置类型

```bash
python3 - <<'PY'
import yaml, pathlib
p = pathlib.Path.home() / ".hermes/config.yaml"
cfg = yaml.safe_load(p.read_text())
for name, conf in cfg.get("mcp_servers", {}).items():
    print(f"{name}: {type(conf).__name__}")
PY
```

所有 MCP server 都应显示 `dict`。

### 7.3 验证 Hermes MCP 列表

```bash
hermes mcp list
```

## 8. 重新加载 MCP

在 Hermes 会话中执行 `/reload-mcp`。

如果第一次仍显示 `'str' object has no attribute 'get'` 但随后出现 `MCP server config changed — reloading connections...` 并成功加载，这是正常恢复过程。

再次执行 `/reload-mcp` 如果显示 `♻️ Reconnected: ... ✅ Agent updated` 则说明已正常。

## 9. 成功判据

1. `hermes mcp list` 正常显示 MCP server 列表
2. 类型检查全部显示 `dict`
3. `/reload-mcp` 不报错
4. 日志出现 `✅ Agent updated`

## 10. 回滚方法

```bash
ls -lt ~/.hermes/config.yaml.bak.* | head
cp ~/.hermes/config.yaml.bak.最近时间 ~/.hermes/config.yaml
hermes mcp list
```

## 11. YAML 通用陷阱补充

本技能聚焦 MCP 字符串配置问题，但系统中还可能遇到其他 YAML 陷阱。

**最常见的非 MCP 陷阱：未引号的冒号**

在 Dify DSL 模板或其他 YAML 中，如果 `source`、`target`、`type` 等字段值包含分号或冒号（如 `task_decomposer; sourceHandle: source`），YAML 会把第二个 `:` 当成 mapping 分隔符，报 `mapping values are not allowed here`。

修复：给包含冒号的标量值加双引号。

```yaml
# 错误
source: task_decomposer; sourceHandle: source

# 正确
source: "task_decomposer; sourceHandle: source"
```

更多 YAML 陷阱详见：`references/yaml-common-pitfalls.md`

## 12. 注意事项

- 不建议用简单 `sed` 修复 JSON 字符串配置
- 推荐用 Python + PyYAML 精准修改具体 MCP 节点
- 修改前必须备份
- 第一次 `/reload-mcp` 失败后自动重载成功是正常过程，不一定需要重启 Gateway
