# SiliconFlow Embedding API

## 端点

`POST https://api.siliconflow.cn/v1/embeddings` （国内站，直连，~0.2s）
`POST https://api.siliconflow.com/v1/embeddings` （国际站，需代理 127.0.0.1:7897，~1.4s）

## 认证

`Authorization: Bearer <api_key>`

⚠ 国内站（siliconflow-cn）和国际站（siliconflow）使用**不同的 API Key**。国内站 key 不能调国际站，反之亦然。

## 可用模型（实测）

| 模型 | 维度 | 最大Token | 状态 |
|------|------|-----------|------|
| `Qwen/Qwen3-Embedding-8B` | 4096 (支持降维到 64/128/256/512/768/1024/2048/4096) | 32768 | ✅ 确认可用 |
| `BAAI/bge-large-zh-v1.5` | 1024 | 512 | ❌ 已下线 |
| `BAAI/bge-m3` | 1024 | 8192 | ❌ 已下线 |
| `netease-youdao/bce-embedding-base_v1` | 768 | 512 | ❌ 已下线 |

**实际上只有 Qwen/Qwen3-Embedding-8B 可用。**

## 请求参数

```json
{
  "model": "Qwen/Qwen3-Embedding-8B",
  "input": ["文本1", "文本2"],
  "encoding_format": "float",
  "dimensions": 1024
}
```

| 参数 | 必填 | 说明 |
|------|------|------|
| `model` | 是 | 仅 `Qwen/Qwen3-Embedding-8B` |
| `input` | 是 | 字符串或字符串数组，不可空 |
| `encoding_format` | 否 | `float` 或 `base64`，默认 `float` |
| `dimensions` | 否 | Qwen3-8B 支持 64/128/256/512/768/1024/2048/4096 |

## 响应

```json
{
  "object": "list",
  "data": [
    {"embedding": [0.123, ...], "index": 0},
    {"embedding": [0.456, ...], "index": 1}
  ],
  "usage": {"prompt_tokens": N, "total_tokens": N}
}
```

## 批量/流控

- 实测单次 POST 可传 50 条文本（`batch_size=50`），~0.2s 返回
- 未遇 429 限流，但建议生产场景每批间隔 0.1s
- 国内站直连时延稳定 ~0.2s，国际站代理 ~1.4s

## 错误码

| 状态码 | 含义 |
|--------|------|
| 200 | 成功 |
| 400 | 模型不存在、输入为空、或账户异常 |
| 401 | API Key 无效（通常是用错站点的 key） |
| 429 | 频率限制 |
