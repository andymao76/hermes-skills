# Copilot ACP Wrapper — 经典 PAT 冲突解决方案

## 问题

`delegate_task(acp_command="copilot")` 会继承父进程的 `GITHUB_TOKEN`（经典 PAT `ghp_`），导致 Copilot CLI 拒绝认证：
```
Error: Classic Personal Access Tokens (ghp_) are not supported by Copilot.
```

## 解决方案

包装器脚本 `~/.hermes/scripts/copilot-acp-wrapper.py`：

```python
#!/usr/bin/env python3
import os, sys, subprocess
token = subprocess.run(['gh', 'auth', 'token'], capture_output=True, text=True).stdout.strip()
env = os.environ.copy()
env['COPILOT_GITHUB_TOKEN'] = token
env.pop('GITHUB_TOKEN', None)
env.pop('GH_TOKEN', None)
os.execve('/home/andymao/.local/bin/copilot', ['copilot'] + sys.argv[1:], env)
```

## 配置

```bash
# 写入 ~/.hermes/.env
echo 'HERMES_COPILOT_ACP_COMMAND=python3 /home/andymao/.hermes/scripts/copilot-acp-wrapper.py' >> ~/.hermes/.env
```

需重启 Hermes 会话使 `.env` 生效。

## 验证

```bash
# 直接测试包装器
python3 ~/.hermes/scripts/copilot-acp-wrapper.py --acp --stdio --version
# → GitHub Copilot CLI 1.0.61.

# ACP 协议测试
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":1}}' | python3 ~/.hermes/scripts/copilot-acp-wrapper.py --acp --stdio
# → {"jsonrpc":"2.0","id":1,"result":{"protocolVersion":1,...}}
```

## 注意事项

- `.env` 的 `GITHUB_TOKEN`（classic PAT `ghp_`）保留给 GitHub MCP 使用，不影响 Copilot
- 包装器只清除环境变量中的 PAT，不修改配置文件
- Session 重启后生效
