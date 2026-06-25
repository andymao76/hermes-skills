# MCP 安全加固 — 实际 sed 命令速查

本文件记录对 `~/.hermes/config.yaml` 中 `mcp_servers` 段进行增删改的精确 sed 命令。

## 安全约束

Agent 不能直接修改 `~/.hermes/config.yaml`（受保护文件）。所有变更必须通过输出 sed 命令让用户执行。

## 删除一个 MCP 服务区块

### 删除 JSON 字符串格式（单行）

如 `github-gov1` 这种写在单行的：

```bash
sed -i '/^  github-gov1:/d' ~/.hermes/config.yaml
```

### 删除多行 YAML 区块

从 `  service:` 到下一个顶级键 `  next-service:`：

```bash
sed -i '/^  old-service:$/,/^  [a-z]/{/^  [a-z]/!d}' ~/.hermes/config.yaml
```

### 两服务之间删除

```bash
sed -i '/^  composio:$/,/^  github-gov1:/{/^  github-gov1:/!d}' ~/.hermes/config.yaml
```

## 新增 MCP 服务

在指定服务行后插入：

```bash
sed -i '/^  github-gov1:/a\  jd:\n    args:\n    - /path/to/server.py\n    command: /path/to/venv/bin/python3\n    connect_timeout: 30\n    timeout: 120' ~/.hermes/config.yaml
```

## 验证

```bash
sed -n '/^mcp_servers:/,/^platform_toolsets:/p' ~/.hermes/config.yaml
grep '^  old-name' ~/.hermes/config.yaml  # 应无输出
```

## .bashrc 清理

```bash
sed -i '172,173d' ~/.bashrc       # 按行号删除
sed -i '/unset TOKEN/d' ~/.bashrc  # 按模式删除
```

## 重载配置

```bash
hermes config reload
# 或
systemctl --user restart hermes-gateway
```
