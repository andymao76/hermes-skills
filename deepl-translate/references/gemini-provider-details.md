# Gemini 模型分层与 SDK 细节

> 创建时间: 2026-06-08, 翻译系统搭建过程中记录

## 模型分层

| 层级 | 模型 | 本机可访问 |
|------|------|-----------|
| 免费层 | gemini-2.5-flash, gemini-2.5-pro, gemini-2.0-flash | ✅ |
| 付费层 | gemini-3.1-pro-preview, gemini-3.5-flash, gemini-3-pro-preview | ❌ 429 limit=0 |

## 双通道访问

### 1. OpenAI 兼容端点
- URL: `https://generativelanguage.googleapis.com/v1beta/openai/chat/completions`
- 轻量，无需额外 SDK
- 翻译简洁直译风格

### 2. google-genai SDK
- 安装: `pip install google-genai --break-system-packages`
- 代理: 必须设 `HTTPS_PROXY=http://127.0.0.1:7897`
- 优点: 模型可选（-m 参数），支持 thinking 等高级功能
- 局限: 翻译偶有未翻译残留（如"拉美"未转写）

## 翻译质量对比 (2026-06-08 实测)

| 原文 | DeepL | Gemini OpenAI | Gemini SDK |
|------|-------|---------------|------------|
| 学好西班牙语，走遍拉美都不怕 | Si aprendes bien el español, podrás viajar por toda Latinoamérica sin ningún problema | Domina el español y recorre Latinoamérica sin miedo | Aprende bien el español, y no tendrás miedo de recorrer Latinoamérica |
| RRC Connection Establishment... | RRC连接建立过程由用户设备（UE）通过三向握手发起 | RRC连接建立过程由UE采用三向握手发起 | — |

## 关键坑

- Gemini 3.x 系列免费层返回 `429 RESOURCE_EXHAUSTED. limit: 0`，需付费
- `max_tokens` 太小会导致空响应（实测 20=空，100=正常）
- SDK 导入需系统 Python（`--break-system-packages`），或 venv Python
