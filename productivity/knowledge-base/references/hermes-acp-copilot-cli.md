# Copilot CLI + Hermes ACP 集成

## 认证流程

1. 确保 gh 已登录（`gh auth status`）
2. 检查是否使用 Classic PAT（`ghp_` 前缀）→ 不支持
3. 解决方法：
   - `unset GITHUB_TOKEN GH_TOKEN` 清除 Classic PAT
   - 重新 `gh auth login --web` 获得 `gho_` 类型 OAuth token
   - 或在 `.env` 设 COPILOT_GITHUB_TOKEN

## ACP 协议测试

```bash
# 基础通信测试
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":1}}' | copilot --acp --stdio
```

成功响应：`{"jsonrpc":"2.0","id":1,"result":{"serverInfo":{"name":"..."}}}`

## Hermes 调用方式

```python
delegate_task(
    goal="...",
    acp_command="copilot",
    acp_args=["--acp", "--stdio"]
)
```

需确保 Hermes 进程环境中有 COPILOT_GITHUB_TOKEN（设为 `.env` 中）。

## 常见问题

| 现象 | 原因 | 解决 |
|------|------|------|
| Classic PAT not supported | GITHUB_TOKEN 含 ghp_ | unset + gh auth login --web |
| Authentication required (ACP) | 子进程未继承环境变量 | 设 `.env` 中的 COPILOT_GITHUB_TOKEN |
| 直连 `-p` 正常但 ACP 失败 | 同上 | 同上 |
