# SiliconFlow + DeepSeek 官方文档知识库

> 2026-06-08 从 https://docs.siliconflow.com/llms-full.txt 及 DeepSeek 官方文档系统性摄取

## 已入库的 10 份 SiliconFlow 手册

| 文件 | 覆盖内容 |
|------|----------|
| `~/knowledge/SiliconFlow_API_使用手册.md` | 端点一览、错误码速查、llms.txt 协议、重要限制 |
| `~/knowledge/SiliconFlow_文本生成_使用手册.md` | Chat Completions、参数调优、消息角色、常见问题 |
| `~/knowledge/SiliconFlow_视觉模型_使用手册.md` | VLM 图片输入、detail 参数、Token 计费公式 |
| `~/knowledge/SiliconFlow_视频生成_使用手册.md` | T2V/I2V、Prompt 规范(200词)、模型列表 |
| `~/knowledge/SiliconFlow_图片生成_使用手册.md` | FLUX 系列、参数、Prompt 技巧 |
| `~/knowledge/SiliconFlow_TTS_使用手册.md` | 8 种预置语音、自定义克隆、动态语音 |
| `~/knowledge/SiliconFlow_推理模型_使用手册.md` | thinking_budget、R1 最佳实践、模型限额表 |
| `~/knowledge/SiliconFlow_交错思维_使用手册.md` | reasoning_content 回传规则、DeepSeek V3.2/GLM-4.7 |
| `~/knowledge/SiliconFlow_FunctionCalling_使用手册.md` | 工具定义、标准流程、天气查询示例 |
| `~/knowledge/SiliconFlow_代码补全_使用手册.md` | FIM (prefix+suffix) + Prefix 补全 |

## 已入库的 5 份 DeepSeek 手册

| 文件 | 覆盖内容 |
|------|----------|
| `~/knowledge/DeepSeek_API_错误码.md` | 400/401/402/422/429/500/503 速查 |
| `~/knowledge/DeepSeek_Token用量计算.md` | 中英文 token 换算、离线 tokenizer |
| `~/knowledge/DeepSeek_首次调用.md` | 思考模式参数、reasoning_effort、thinking.type |
| `~/knowledge/DeepSeek_API_完整参考.md` | 全量文档：思考模式、Tool Calls(strict)、FIM、JSON Output、多轮对话、上下文硬盘缓存、限速与隔离、Anthropic API 兼容 |
| `~/knowledge/DeepSeek_Agent工具接入.md` | CodeWhale + SiliconFlow 集成

## 已入库的 1 份 Hermes 集成手册

| 文件 | 覆盖内容 |
|------|----------|
| `~/knowledge/SiliconFlow_Hermes集成.md` | SiliconFlow 官方 Hermes Agent 接入指南 |

## 已配置的 Tokenizer

DeepSeek V3 Tokenizer 已安装于 `/tmp/deepseek_v3_tokenizer/`，脚本位于 `~/.hermes/scripts/deepseek-tokenizer`。
用法: `echo "文本" | python3 ~/.hermes/scripts/deepseek-tokenizer`

## 文档摄取模式

用户粘贴官方文档片段 + "学习这个文档" → Agent 提取核心信息 → 精简为结构化 Markdown → 写入 `~/knowledge/` → 记录到此索引。
