# SiliconFlow 推理模型 (Reasoning)

## 支持模型

| 系列 | 模型 |
|------|------|
| DeepSeek | R1 (163K ctx), R1-Distill-Qwen-32B/14B/1.5B |
| Qwen | Qwen3-235B, Qwen3-32B/14B/8B, QwQ-32B |
| GLM | GLM-Z1-32B, GLM-Z1-9B |
| MiniMax | MiniMaxAI/MiniMax-M2.1 |
| Tencent | Hunyuan-A13B |

## 关键参数

- `thinking_budget`: 推理链最大token数，通过 `extra_body={"thinking_budget": 1024}` 传递
- 返回双字段: `reasoning_content` (推理过程) + `content` (答案)

## DeepSeek-R1 最佳实践

- temperature: **0.6** (范围 0.5~0.7)
- top_p: **0.95**
- **不要加 system prompt**，所有指令写 user prompt
- 数学题: "Please reason step by step, put final answer in \\boxed{}"

## 截断规则

| 情形 | 行为 |
|------|------|
| 推理链达 thinking_budget | Qwen3 强制停止，其他可能继续 |
| 响应超 max_tokens | 截断，finish_reason="length" |

## 代码示例

```python
from openai import OpenAI
client = OpenAI(api_key="KEY", base_url="https://api.siliconflow.com/v1")

response = client.chat.completions.create(
    model="deepseek-ai/DeepSeek-R1",
    messages=[{"role": "user", "content": "9.11和9.8哪个大？"}],
    stream=True, max_tokens=4096,
    extra_body={"thinking_budget": 1024}
)

for chunk in response:
    if chunk.choices[0].delta.reasoning_content:
        print(chunk.choices[0].delta.reasoning_content)  # 思考过程
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content)             # 答案
```
