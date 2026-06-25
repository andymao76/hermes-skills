# _build_safe_env() 环境变量过滤详解

## 代码位置

`~/.hermes/hermes-agent/tools/mcp_tool.py`

## 白名单定义（约 267-301 行）

```python
_SAFE_ENV_KEYS = frozenset({
    "PATH", "HOME", "USER", "LANG", "LC_ALL", "TERM", "SHELL", "TMPDIR",
})

_SAFE_ENV_KEYS_CASE_INSENSITIVE = frozenset({
    # Windows only（Linux 下不生效）
    "ALLUSERSPROFILE", "APPDATA", "COMMONPROGRAMFILES", ...
})
```

仅 8 个 Linux 环境变量通过 + 所有 `XDG_*` 前缀的变量。

## _build_safe_env() 逻辑（约 328-348 行）

```python
def _build_safe_env(user_env: Optional[dict]) -> dict:
    env = {}
    for key, value in os.environ.items():
        if (
            key in _SAFE_ENV_KEYS
            or key.upper() in _SAFE_ENV_KEYS_CASE_INSENSITIVE
            or key.startswith("XDG_")
        ):
            env[key] = value
    if user_env:          # ← config.yaml 的 env: 段
        env.update(user_env)
    return env
```

关键点：`user_env`（config.yaml 的 `env:` 段）在过滤后追加，**不受白名单限制**。但如果 config.yaml 中没有 `env:` 段，所有非白名单 env var 均被丢弃。

## 诊断方法

### 1. 创建 debug wrapper 捕获子进程环境

```bash
cat > /tmp/debug-wrapper.sh << 'SCRIPT'
#!/bin/bash
env | sort > /tmp/mcp-env-dump-$$.txt
echo "ENV DUMPED: PID=$$" >> /tmp/mcp-env-dump-$$.txt
exec /path/to/binary "$@"
SCRIPT
chmod +x /tmp/debug-wrapper.sh
```

临时修改 config.yaml，将目标 MCP 的 `command` 指向调试 wrapper，然后运行 `hermes mcp test 服务名`。

检查 `/tmp/mcp-env-dump-*.txt`，对比当前 shell 的 `env | grep -i token` 输出。

### 2. 直接 pipe 测试（不经过 Hermes MCP 客户端）

```bash
export GITHUB_PERSONAL_ACCESS_TOKEN="your_token_here"
printf '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}\n' | \
  timeout 10 /path/to/binary stdio 2>/dev/null | head -3
```

如果返回包含 `"result":{"capabilities":...}` 的 JSON-RPC 响应，说明二进制本身和 token 都没问题。

## 已知受影响的服务模式

| 模式 | 场景 | 症状 |
|------|------|------|
| wrapper 脚本 + env | wrapper 从 `.bashrc` 读取 `$TOKEN` | "Connection closed" |
| 直接二进制 + env | 二进制读取 `$GITHUB_TOKEN` | "Connection closed" |
| 无 token | 二进制启动但无认证 | 401/403 响应 |
