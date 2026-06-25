---
name: siliconflow
description: SiliconFlow API 完整参考 — 文本生成/视觉/视频/图片/TTS/推理/嵌入，覆盖端点、参数、模型、计费和排错。
category: mlops
tags: [siliconflow, llm, vlm, tts, image-generation, video-generation, reasoning]
---

# SiliconFlow API 技能

## 触发条件

用户提到 SiliconFlow、硅基流动、硅流、或使用 `/model siliconflow` 时加载。也适用于图片生成、视频生成、TTS、VLM 等 SiliconFlow 特有能力的咨询。

## 基本信息

| 项目 | 值 |
|------|-----|
| 端点 | `https://api.siliconflow.com/v1` |
| 兼容性 | OpenAI 兼容 (chat/completions, embeddings, images, audio) |
| 代理 | 国际站需要 (HTTPS_PROXY=http://127.0.0.1:7897)；国内站 api.siliconflow.cn 直连，时延低 5x |
| llms.txt | https://docs.siliconflow.com/llms.txt |
| 体验 | https://cloud.siliconflow.com/playground |
| 模型列表 | https://cloud.siliconflow.com/models |

## 能力矩阵

| 能力 | 端点 | 关键模型 | 参考文档 |
|------|------|----------|----------|
| 文本生成 | /chat/completions | DeepSeek-V3/V4, Qwen3.x | `references/text-generation.md` |
| 推理 | /chat/completions | DeepSeek-R1, QwQ-32B | `references/reasoning.md` |
| 文本嵌入 | /embeddings | `Qwen/Qwen3-Embedding-8B` (4096/1024/512dim) | `references/embeddings.md` |
| 视觉(VLM) | /chat/completions | Qwen3-VL-32B, Qwen3-VL-8B, Qwen3-VL-30B-A3B | `references/vision.md` |
| 图片生成 | /images/generations | FLUX.1-dev/schnell/pro | `references/image-generation.md` |
| 视频生成 | /video/submit → /video/status | Wan2.1-T2V, Wan2.2-I2V | `references/video-generation.md` |
| 语音合成 | /audio/speech | CosyVoice2-0.5B, fish-speech-1.5 | `references/text-to-speech.md` |

## 本机配置

国际站 (config.yaml):
```yaml
providers:
  siliconflow:
    api_key: sk-ybh...etvn         # 国际站 key
    base_url: https://api.siliconflow.com/v1
    model: Qwen/Qwen3.6-35B-A3B
```

国内站 (config.yaml):
```yaml
providers:
  siliconflow-cn:
    api_key: sk-swy...vrnf         # 国内站 key (不同)
    base_url: https://api.siliconflow.cn/v1
    default: Qwen/Qwen3.5-397B-A17B
```

## 双站点架构

本环境同时配置了国际站和国内站：

| 站点 | 端点 | 时延(本机) | 代理 |
|------|------|-----------|------|
| **国际站** | `https://api.siliconflow.com/v1` | ~2600ms | 需要 (127.0.0.1:7897) |
| **国内站** | `https://api.siliconflow.cn/v1` | ~515ms | 直连 |

国内站模型列表与国际站基本相同（93+ 模型，含 Qwen/DeepSeek 全系列），直连时延低 5 倍，优先使用国内站。余额可通过 `hermes chat -q "查余额" --provider siliconflow-cn` 查看。

## 注意事项

- **图片 URL 1小时过期**，生成后立即下载
- **视频结果 10分钟过期**，需轮询 status 端点
- **错误 429** = 频率限制，指数退避重试
- **错误 503/504** = 服务端过载，切备用模型或 stream=true
- **max_tokens** 预留 ~10k 给输入，不要设为上下文全长度
- **输出乱码** 设 temperature=0.7, top_k=50, top_p=0.7
- **vision_analyze 可能失败**：当前模型（如 DeepSeek）不支持原生视觉，Hermes 的视觉后备模型也可能报 `unknown variant image_url`。此时用 Python 脚本直接调用 SiliconFlow VLM API（见 `references/vision.md` 备用方案），从 config.yaml 正则提取完整 key。**也尝试阿里百炼 Qwen-VL**（`references/bailian-vision-alternative.md`），双 provider 保障。
- **临时切换 auxiliary.vision 到 SiliconFlow**：执行 `hermes config set auxiliary.vision.provider siliconflow-cn && hermes config set auxiliary.vision.model Qwen/Qwen3-VL-32B-Instruct && hermes config set auxiliary.vision.base_url https://api.siliconflow.cn/v1`。注意：如果 provider 的 `api_key` 为空字符串且依赖 `api_key_env`，需要在 `auxiliary.vision` 下显式设置 `api_key`（用 `printenv`+临时文件法读取 env 后写入配置）。使用后建议恢复原始配置（deepseek + deepseek-v4-pro）。

## DeepSeek-R1 专门注意

- temperature: 0.6 (推荐), top_p: 0.95
- **不要加 system prompt**
- thinking_budget 通过 `extra_body={"thinking_budget": 1024}` 传递
- reasoning_content 与 content 同级返回
