# SiliconFlow 多模态视觉模型参考

> 收录在 SiliconFlow (api.siliconflow.com) 上经过验证的多模态/视觉语言模型。
> 更新日期：2026-06-05

## 旗舰视觉模型

| 模型 | 架构 | 参数 | 上下文 | SiliconFlow 定价 (per M tokens) | 特点 |
|------|------|------|--------|------|------|
| **Qwen3.6-35B-A3B** | MoE | 35B总/3B激活 | 256K (可扩展~1M) | - | 统一图文视频理解，超越GPT-5-mini，含思维模式 |
| **GLM-4.5V** | MoE | 106B总/12B激活 | 66K | $0.14 input / $0.86 output | 41项基准SOTA，3D-RoPE空间推理，思考模式开关 |
| **Qwen3-VL-32B-Instruct** | Dense | 32B | 131K | $0.27/M | 视觉代理能力强，文档分析，工具调用 |
| **Kimi K2.6** | MoE | 1T总/32B激活 | 256K | - | 月之暗面，原生多模态，4000+工具调用，智能体场景 |
| **GLM-4.1V-9B-Thinking** | Dense | 9B | 66K | $0.035 input / $0.14 output | 9B媲美72B性能，4K图像支持，性价比之王 |
| **Qwen2.5-VL-32B-Instruct** | Dense | 32B | 131K | $0.27/M | 成熟稳定，视觉代理，文档布局分析 |

## 测试通过的模型

以下模型已通过 `hermes chat -q` 连通性测试并可正常使用：

- ✅ **Qwen/Qwen3.6-35B-A3B** — 2026-06-05 测试通过，是当前主力模型

## 按使用场景推荐

### 需要强图像/视频理解（多模态任务）
1. **Qwen3.6-35B-A3B** ← 首推，统一视觉语言，最新旗舰
2. **GLM-4.5V** — 独立多模态架构，41项基准SOTA
3. **Kimi K2.6** — 智能体+多模态场景

### 文档/OCR/布局分析
1. **Qwen3-VL-32B-Instruct** — 131K上下文，结构化输出
2. **Qwen2.5-VL-32B-Instruct** — 成熟稳定

### 成本敏感/轻量场景
1. **GLM-4.1V-9B-Thinking** — $0.14/M output，9B胜72B
2. **Qwen3.6-35B-A3B** — MoE高效，仅3B激活

## 注意事项

- 所有 SiliconFlow 国际站模型均需通过代理 `127.0.0.1:7897` 访问
- 模型 ID 格式为 `Vendor/ModelName`（如 `Qwen/Qwen3.6-35B-A3B`）
- DeepSeek 系列模型为纯文本模型，不支持图像输入
- 切换模型后需 `hermes config set model provider/ModelName` 并更新 provider 字段
