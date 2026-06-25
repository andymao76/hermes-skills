# 渠道说明

## Telegram

### 语音支持
- ✅ 发语音消息 → 支持接收 OPUS 格式音频
- ✅ 回语音消息 → 支持发送 OGG/MP3 格式音频

### 配置建议

```yaml
channels:
  telegram:
    messages:
      tts:
        auto: "inbound"
        provider: edge
        voice: "zh-CN-XiaoxiaoNeural"
```

### 注意事项
- Telegram 语音消息自动以 OPUS 格式发送
- 如果使用 OpenAI TTS，返回 MP3 格式
- 长语音建议分段（每条 < 30 秒）

---

## 飞书 (Lark/Feishu)

### 语音支持
- ✅ 发语音消息 → 支持接收（需配置飞书应用）
- ✅ 回语音消息 → 需要 AMR-WB 格式转换

### 配置建议

```yaml
channels:
  feishu:
    messages:
      tts:
        auto: "inbound"
        provider: edge
        voice: "zh-CN-XiaoxiaoNeural"
```

### 注意事项
- 飞书语音消息默认 AMR-WB 编码
- 回复语音需要格式转换（opus → amr）
- 飞书语音文件大小限制：< 2MB

---

## 其他渠道

| 渠道 | 语音输入 | 语音输出 | 备注 |
|------|---------|---------|------|
| Discord | ✅ | ✅ | 支持 OPUS 格式 |
| WhatsApp | ✅ | ✅ | 支持 OGG 格式 |
| WeChat | ✅ | ⚠️ 有限 | 需要微信官方接口权限 |
| SMS | ❌ | ❌ | 不支持语音 |
