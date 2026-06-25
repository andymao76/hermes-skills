# Gateway 配置代码片段

## messages.tts 配置参考

### 自动语音回复（关键开关）

```yaml
messages:
  tts:
    # 可选值：
    #   "never"    — 从不自动语音回复
    #   "inbound"  — 仅回复语音消息（用户说语音→Agent回语音）
    #   "all"      — 所有消息都回语音
    auto: "inbound"
    
    # TTS 后端（从已配置的 TTS provider 中选）
    provider: edge   # 可选: edge, openai, elevenlabs 等
    
    # 语音偏好
    voice: "zh-CN-XiaoxiaoNeural"  # Edge TTS 中文女声
    
    # 语音回复最大时长（秒），超长内容自动截断
    max_duration: 30
    
    # 语速倍率（0.5-2.0）
    rate: 1.0
    
    # 音量倍率（0.0-1.0）
    volume: 1.0
```

### Platform 级覆盖

对特定平台（如 Telegram）单独配置：

```yaml
channels:
  telegram:
    messages:
      tts:
        auto: "inbound"
        provider: edge
        voice: "zh-CN-XiaoxiaoNeural"
```

### 仅文字不语音的场景

```yaml
messages:
  tts:
    auto: "never"   # 关闭自动语音
```

## 注意事项

1. `auto: "inbound"` 是最常见的配置——用户发语音才回语音，保持正常文字交互
2. Edge TTS 无需 API Key，免费使用，适合大多数场景
3. 语音文件会缓存到 `~/.hermes/audio_cache/`，可定期清理
4. 长语音消息超过 `max_duration` 会被截断，建议拆分发送
5. 测试方式：发一条语音消息 + 一条文字消息，观察回复差异
