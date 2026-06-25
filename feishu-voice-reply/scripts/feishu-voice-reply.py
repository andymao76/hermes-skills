#!/usr/bin/env python3
"""
feishu-voice-reply.py — 飞书语音回复封装

流程:
  1. 使用 Edge TTS 生成 MP3 语音文件
  2. 输出 MEDIA 路径供飞书发送

用法:
  python feishu-voice-reply.py <文本> [声音]
  声音: xiaoxiao(默认) / xiaoyi / yunyang / yunxi / yunze

输出:
  MEDIA:/tmp/feishu-voice-xxx.mp3   ← 用于飞书语音消息
"""

import asyncio
import os
import sys
import tempfile

try:
    import edge_tts
except ImportError:
    print("请先安装 edge-tts: pip3 install edge-tts", file=sys.stderr)
    sys.exit(1)

VOICES = {
    "xiaoxiao": "zh-CN-XiaoxiaoNeural",
    "xiaoyi": "zh-CN-XiaoyiNeural",
    "yunyang": "zh-CN-YunyangNeural",
    "yunxi": "zh-CN-YunxiNeural",
    "yunze": "zh-CN-YunzeNeural",
}


async def main():
    if len(sys.argv) < 2:
        print("用法: feishu-voice-reply.py <文本> [声音]", file=sys.stderr)
        sys.exit(1)

    text = sys.argv[1]
    voice_name = sys.argv[2] if len(sys.argv) > 2 else "xiaoxiao"

    voice = VOICES.get(voice_name)
    if not voice:
        print(f"错误: 不支持的声音 '{voice_name}'", file=sys.stderr)
        sys.exit(1)

    # 生成语音到临时文件
    output_path = f"/tmp/feishu-voice-{os.getpid()}.mp3"
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)

    if os.path.isfile(output_path):
        # 输出 MEDIA 路径供飞书发送
        print(f"MEDIA:{output_path}")
    else:
        print("错误: 语音生成失败", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
