# 翻译引擎对比实录 (2026-06-08)

## 测试语料

| 原文 | 类型 |
|------|------|
| "学会西语用处大，找个本地女朋友吧" | 日常对话 |
| "学好西班牙语，走遍拉美都不怕" | 日常对话 |
| 3GPP TS 25.331 第5-6节 (~1000字) | 技术规范 |
| "太好了" | 短句 |

## 三引擎对比

### DeepL
- 风格：地道意译，自然流畅
- 术语：保留缩写，首次出现的术语不展开
- 西语："Aprender español te será muy útil; ¿por qué no te buscas una novia de allí?"
- 优点：技术文档术语一致性最好
- 缺点：无上下文定制能力（system prompt 不支持）
- 配额：50万字符/月，每月14日重置
- 代理：不需要

### Gemini OpenAI 兼容
- 风格：直译简洁
- 术语：保留缩写
- 西语："Aprender español es muy útil, búscate una novia local."
- 优点：支持 system prompt 定制翻译风格
- 缺点：响应偶尔啰嗦（如提供多个翻译选项+解释）
- 配额：Google 免费层
- 代理：需要 127.0.0.1:7897

### Gemini google-genai SDK
- 风格：与 OpenAI 兼容模式相似
- 西语："Aprende bien el español, y no tendrás miedo de recorrer Latinoamérica."
- 优点：原生 SDK，支持更多模型参数
- 缺点："拉美"一次未翻译为"Latinoamérica"（2.5-flash）
- 可用模型：2.5-flash(免费), 2.5-pro(免费), 3.1-pro-preview(付费)

## 3GPP 技术文档翻译评估

| 维度 | DeepL | Gemini |
|------|-------|--------|
| 术语保留 | ★★★★★ | ★★★★★ |
| 协议消息名 | ★★★★☆ | ★★★★☆ |
| 流程描述 | ★★★★★ | ★★★★ |
| IE 名称 | ★★★★☆ | ★★★★ |
| 规范用语 | ★★★★★ | ★★★★ |

## 选型建议

| 场景 | 推荐 |
|------|------|
| 技术规范/协议文档 | DeepL |
| 日常对话 | DeepL |
| 需要调整风格/上下文 | Gemini |
| 大批量文档 | DeepL (上传PDF) |
