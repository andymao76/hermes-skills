---
name: voice-reply-mode
description: 语音回复模式 — 用户发语音→Agent回语音，用户发文字→Agent回文字。包含SOUL.md/IDENTITY.md/TOOLS.md行为规则、Edge TTS脚本、Gateway配置代码片段、Telegram/飞书渠道说明。
---

# 语音回复模式

当用户希望 Agent 表现以下行为时，使用此技能：

- 用户发语音 → Agent 回语音
- 用户发文字 → Agent 回文字

## 此技能包含的内容

- SOUL.md / IDENTITY.md / TOOLS.md 的工作区级行为规则
- 可复用的 Edge TTS 辅助脚本
- `messages.tts` 的 Gateway 配置代码片段
- Telegram / 飞书风格部署的渠道说明

## 重要边界

此技能可以打包规则、脚本和配置代码片段。

**除非用户明确要求并授权，否则不会自动更改用户的全局 Gateway 配置。**

## 推荐工作流程

1. 阅读 `references/workspace-snippets.md`
2. 阅读 `references/gateway-config.md`
3. 将相关代码片段复制到目标 Agent 工作区
4. **如果用户明确要求**，使用 `references/gateway-config.md` 中的代码片段修补 Gateway 配置
5. 用一条文字消息和一条语音消息进行验证

## 最低成功标准

- 文字消息收到文字回复
- 语音消息收到语音回复
- Agent 工作区记录偏好的语音

## 注意事项

- 在许多部署中，决定性的开关是 Gateway 级别的 `messages.tts.auto = "inbound"`
- 工作区文件定义行为预期，但 Gateway 配置决定自动语音回复是否实际发生
- 如果 schema 拒绝 `identity.voice`，请将语音偏好记录在工作区文档中
