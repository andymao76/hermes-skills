# SiliconFlow 文本生成

## 核心参数

| 参数 | 范围 | 建议值 | 说明 |
|------|------|--------|------|
| temperature | 0.0~2.0 | 0.5~0.7 | 越高越有创意 |
| top_p | 0~1 | 0.9 | 核采样 |
| max_tokens | - | 预留10k给输入 | 不要设满上下文长度 |
| frequency_penalty | -2.0~2.0 | 0.5 | 抑制重复 |
| stream | bool | 长输出推荐true | 防止504超时 |

## 消息角色

| 角色 | 作用 |
|------|------|
| system | 定义AI角色和行为 |
| user | 用户输入 |
| assistant | 历史回复/示例 |

## 常见问题

| 问题 | 解法 |
|------|------|
| 输出乱码 | temperature=0.7, top_k=50, top_p=0.7, frequency_penalty=0 |
| 输出截断 | 增加max_tokens + stream=true + 客户端超时 |
| 504超时 | 非流式长输出易超时，用stream=true |
| 429频率限制 | 指数退避重试 |
| 503/504服务过载 | 切备用模型 |

## 代码示例

```python
from openai import OpenAI
client = OpenAI(api_key="KEY", base_url="https://api.siliconflow.com/v1")
response = client.chat.completions.create(
    model="deepseek-ai/DeepSeek-V3",
    messages=[{"role": "user", "content": "你好"}],
    temperature=0.7, max_tokens=1024, stream=True
)
```

## 模型推荐

| 场景 | 推荐模型 |
|------|----------|
| 通用对话 | DeepSeek-V3/V4, Qwen3.5/3.6 |
| 代码生成 | Qwen2.5-Coder-32B-Instruct |
| JSON输出 | DeepSeek-V2.5 (response_format={"type":"json_object"}) |
| 数据分析 | QVQ-72B-Preview |

计费: 总费用 = (输入Token × 输入单价) + (输出Token × 输出单价)
