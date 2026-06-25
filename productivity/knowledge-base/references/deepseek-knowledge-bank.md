# DeepSeek API 知识库索引

> 已摄入文件列表（~/knowledge/）

| 文件 | 内容 |
|------|------|
| DeepSeek_API_完整参考.md | 全 API 参考（思考模式/Tool Calls/JSON/FIM/缓存/Anthropic/限速） |
| DeepSeek_首次调用.md | base_url、模型名、思考模式参数 |
| DeepSeek_API_错误码.md | 400/401/402/422/429/500/503 |
| DeepSeek_Token用量计算.md | 英 0.3/中 0.6 token/字符 |

## 关键要点

- 两个 base_url: OpenAI 格式 `api.deepseek.com`，Anthropic 格式 `api.deepseek.com/anthropic`
- 模型: deepseek-v4-pro（主力）, deepseek-v4-flash（快速）
- 思考模式: `reasoning_effort="high"` + `extra_body={"thinking":{"type":"enabled"}}`
- 有 tool_calls 时必须原样回传 reasoning_content
- 上下文缓存默认开启，命中规则：完整匹配缓存前缀单元
- 用户 ID 隔离: `extra_body={"user_id": "xxx"}`
- Batch API 半价
- 本机 config.yaml 已配置 deepseek provider
