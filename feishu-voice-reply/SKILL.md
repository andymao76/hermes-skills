---
name: feishu-voice-reply
description: 自动将文本转换为飞书原生语音消息并发送，支持波形播放。
  使用微软 Edge Neural TTS 引擎（edge-tts），免费无需 API Key。
  支持多种中文声音（xiaoxiao, xiaoyi, yunyang 等）。
category: productivity
---

# 飞书语音回复技能

自动将文本转换为飞书原生语音消息并发送，支持波形播放格式。

## 适用场景

- 希望收到语音回复时
- 需要更自然的对话体验时
- 想要发送语音通知时

## 核心组件

### 1. Edge TTS 语音生成
- 使用微软 Edge Neural TTS 引擎
- 支持多种声音（xiaoxiao, xiaoyi, yunyang 等）
- 完全免费，无需 API Key

### 2. 飞书语音发送
- 飞书原生语音格式（msg_type: audio）
- 支持私聊和群聊
- 波形播放显示

## 支持的声音

| 声音 | 性别 | 特点 | 推荐场景 |
|------|------|------|----------|
| xiaoxiao | 女 | 活泼专业 | ⭐⭐⭐⭐⭐ 通用 |
| xiaoyi | 女 | 温柔亲切 | ⭐⭐⭐⭐ 情感类 |
| yunyang | 男 | 沉稳 | ⭐⭐⭐ 正式 |
| yunxi | 男 | 北京话 | ⭐⭐⭐ 幽默 |
| yunze | 男 | 活力 | ⭐⭐⭐ 年轻 |

## 安装

```bash
pip3 install edge-tts
# 国内镜像加速
pip3 install edge-tts -i https://pypi.tuna.tsinghua.edu.cn/simple
```

> **Ubuntu 24.04 踩坑**：系统启用了 PEP 668 外部环境保护，`pip3 install` 会拒绝写入全局 site-packages。加 `--break-system-packages` 绕过：
> ```bash
> pip3 install edge-tts --break-system-packages
> ```

## 用法

```bash
# 生成语音文件
python {skill_dir}/scripts/edge_tts_async.py "你好世界" xiaoxiao /tmp/voice.mp3

# 或使用封装脚本
python {skill_dir}/scripts/feishu-voice-reply.py "要朗读的文本" xiaoxiao
```

## 核心规则（语音发送后绝对静默）

> ⚠️ 语音发送后，**绝对不做任何回复操作！**
> 不发送文字消息、不确认"已发送"、不加任何表情符号。
> 语音发送后立即彻底停止。唯一例外：语音生成失败时用文字说明。

## 依赖

- Python 3.7+
- edge-tts（官方 PyPI）
- ffmpeg（可选，用于格式转换）

## 性能

- 语音生成速度：3-5 秒（100 字）
- 音频质量：高（微软 Neural）
- 文件大小：20-30 KB（每 100 字）
- 成本：完全免费
