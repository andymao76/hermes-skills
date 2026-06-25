#!/usr/bin/env python3
"""
edge_tts_async.py — Edge TTS 语音生成

使用微软 Edge Neural TTS 引擎生成语音文件。
完全免费，无需 API Key。

用法:
  python edge_tts_async.py <文本> [声音] [输出路径]

参数:
  文本    - 要朗读的文字内容
  声音    - xiaoxiao(默认) / xiaoyi / yunyang / yunxi / yunze
  输出路径 - 音频文件保存路径 (默认 /tmp/edge_tts_output.mp3)
"""

import asyncio
import sys

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
        print("用法: edge_tts_async.py <文本> [声音] [输出路径]", file=sys.stderr)
        sys.exit(1)

    text = sys.argv[1]
    voice_name = sys.argv[2] if len(sys.argv) > 2 else "xiaoxiao"
    output_path = sys.argv[3] if len(sys.argv) > 3 else "/tmp/edge_tts_output.mp3"

    voice = VOICES.get(voice_name)
    if not voice:
        print(f"错误: 不支持的声音 '{voice_name}'，可选: {', '.join(VOICES.keys())}", file=sys.stderr)
        sys.exit(1)

    print(f"[edge-tts] 声音={voice_name}, 文本长度={len(text)}字", file=sys.stderr)
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)

    print(f"[edge-tts] 完成: {output_path}", file=sys.stderr)
    print(output_path)


if __name__ == "__main__":
    asyncio.run(main())
