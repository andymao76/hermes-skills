# OpenAI Provider 配置坑点与排查记录

## 核心事实：`openai` 被 ALIASES 映射到 `openrouter`

在 Hermes Agent v0.14.0（2026.5.16）中，`hermes_cli/providers.py` 的 `ALIASES` 字典定义：

```python
ALIASES = {
    "openai": "openrouter",  # bare "openai" → route through aggregator
    ...
}
```

这意味着：
- `--provider openai` → 实际解析为 openrouter
- `config.yaml` 中 `model.provider: openai` → 同样被映射到 openrouter
- 如果没有配置 `OPENROUTER_API_KEY`，会报 `Unknown provider 'openai'`

## Provider 名称对照

| 写错的名 | 实际映射到 | 说明 |
|----------|-----------|------|
| `openai` | `openrouter` | ALIASES 硬编码映射 |
| `openai-codex` | 自身（`codex_responses` transport） | 指向 `chatgpt.com/backend-api/codex`，不是标准 Chat API |
| 不设（`auto`） | 自动检测 | 有 `OPENAI_API_KEY` 时应能检测到，但实战中不稳定 |

## 安全使用 OpenAI Chat API 的方案

### 方案 A：不设特定 provider，依赖自动检测

在 config.yaml 中设置 `model.provider: auto`（或删除这一行），hermes 会自动尝试识别可用 provider。但实战中自动检测可能失败，导致 `Initializing agent...` 后无响应。

### 方案 B：使用自定义 provider（不受 ALIASES 影响）

在 config.yaml 中创建自定义 provider，绕开 ALIASES：

```yaml
providers:
  openai-direct:
    api_key: YOUR_OPENAI_KEY      # 从 .env 中读取
    base_url: https://api.openai.com/v1
    default: gpt-4o
    model: gpt-4o
```

**但需要注意**：自定义 provider 的 name（如 `openai-direct`）会被 `resolve_provider_full` 作为自定义 provider 解析，但这取决于 hermes 对自定义 provider 的支持程度。

### 方案 C：直接使用 OpenAI SDK / curl（绕过 hermes provider 系统）

```bash
OPENAI_KEY=$(grep '^OPENAI_API_KEY=' ~/.hermes/.env | head -1 | sed 's/OPENAI_API_KEY=//')
curl -s https://api.openai.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENAI_KEY" \
  -d '{"model": "gpt-4o", "messages": [{"role": "user", "content": "hi"}], "max_tokens": 50}'
```

## 排查路径速查

当 `hermes chat` 报 `Unknown provider 'openai'` 时：

1. **检查 ALIASES**：`grep -A1 '"openai"' /path/to/hermes/hermes_cli/providers.py`
2. **检查 provider 映射**：`python3 -c "from hermes_cli.providers import get_provider; p=get_provider('openai'); print(p.id if p else None)"`
3. **检查 models.dev**：`python3 -c "from agent.models_dev import get_model_info; info=get_model_info('openai', 'gpt-4o'); print(info.provider_id if info else 'not found')"`
4. **直接测试 API**：用 curl 测试 API key 是否有效（见方案 C）
5. **检查配额**：如果 API 返回 `insufficient_quota`，说明 key 有效但需要充值

## API Key 截断警告

`write_file` 和 `patch` 工具在 hermes 中可以截断长 API key（`sk-pro...0LwA` 这种形式）。修复方法：
- 从 `.env` 中读取完整 key：`grep '^OPENAI_API_KEY=' ~/.hermes/.env | sed 's/OPENAI_API_KEY=//'`
- 用 `python3` 在 `.env` 中读取后写入 config.yaml（不要用 patch）
- 避免用 patch 修改包含 API key 的 YAML 字段
