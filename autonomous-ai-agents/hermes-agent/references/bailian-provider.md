# 阿里云百炼 (Bailian) Provider 配置指南

## 概述

阿里云百炼是阿里巴巴的大模型服务平台，提供通义千问 (Qwen) 系列模型的 API 访问。

**API 兼容性：** OpenAI 兼容模式 (`/compatible-mode/v1/`)

---

## 快速配置

### 1. 添加 API Key 到 .env

```bash
echo 'DASHSCOPE_API_KEY=sk-your-key-here' >> ~/.hermes/.env
```

### 2. 配置 Provider

```bash
hermes config set providers.bailian.api_key sk-your-key-here
hermes config set providers.bailian.base_url https://dashscope.aliyuncs.com/compatible-mode/v1
hermes config set providers.bailian.default qwen-plus
```

### 3. 切换到百炼模型

```bash
# 临时使用
hermes chat -q "问题" --provider bailian --model qwen-plus

# 或切换默认配置
hermes config set model.provider bailian
hermes config set model.model qwen-plus
```

---

## 可用模型

| 模型 | 说明 | 适用场景 |
|------|------|----------|
| `qwen-plus` | 均衡型，性价比高 | 日常对话、一般任务 |
| `qwen-max` | 最强能力 | 复杂推理、代码生成 |
| `qwen-turbo` | 快速响应 | 简单问答、实时交互 |
| `qwen-long` | 长上下文 | 长文档分析 |

---

## API 测试

### 使用 curl 直接测试

```bash
curl -s -X POST "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $DASHSCOPE_API_KEY" \
  -d '{"model":"qwen-plus","messages":[{"role":"user","content":"Hello"}]}'
```

预期响应：
```json
{
  "model": "qwen-plus",
  "choices": [{"message": {"content": "...", "role": "assistant"}}],
  "usage": {"total_tokens": N}
}
```

### 通过 Hermes CLI 测试

```bash
hermes chat -q "用一句话测试" --provider bailian --model qwen-plus
```

---

## 定价参考

- **qwen-plus**: 约 ¥0.004/1K tokens (输入), ¥0.012/1K tokens (输出)
- **qwen-max**: 约 ¥0.04/1K tokens (输入), ¥0.12/1K tokens (输出)
- **qwen-turbo**: 约 ¥0.002/1K tokens (输入), ¥0.006/1K tokens (输出)

(价格可能变动，请以阿里云官网为准)

---

## 常见问题

### 1. 401 Unauthorized

检查 API Key 是否正确，确保 `DASHSCOPE_API_KEY` 环境变量已设置。

### 2. 模型不可用

某些模型可能需要单独开通。登录阿里云百炼控制台确认模型状态。

### 3. 响应慢

国内直连通常很快。如遇到延迟，检查网络连接或尝试 `qwen-turbo`。

---

## 与 SiliconFlow 上的 Qwen 对比

| 特性 | 阿里云百炼 | SiliconFlow |
|------|------------|-------------|
| 模型命名 | `qwen-plus`, `qwen-max` | `Qwen/Qwen3.5-397B-A17B` |
| 网络 | 国内直连 | 需代理 (国际站) |
| 延迟 | 低 | 较高 |
| 价格 | 按量计费 | 按量计费 |
| 最新模型 | 优先上线 | 稍有延迟 |

**建议：** 国内环境优先使用阿里云百炼，响应更快且无需代理。

---

## 参考资料

- 阿里云百炼控制台：https://bailian.console.aliyun.com/
- API 文档：https://help.aliyun.com/zh/model-studio/
- 模型列表：https://www.alibabacloud.com/help/zh/model-studio/models