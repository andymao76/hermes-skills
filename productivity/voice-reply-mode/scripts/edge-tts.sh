#!/bin/bash
# Edge TTS 辅助脚本 — 本地文本转语音
# 依赖: edge-tts (pip install edge-tts)
#
# 用法:
#   ./edge-tts.sh "你好，欢迎使用语音回复模式"
#   ./edge-tts.sh -v "zh-CN-YunxiNeural" "这段文字用男声朗读"
#   ./edge-tts.sh -o /tmp/output.mp3 "保存到指定文件"

set -euo pipefail

# 默认值
VOICE="zh-CN-XiaoxiaoNeural"
OUTPUT=""
RATE="+0%"
VOLUME="+0%"

# 解析参数
while getopts "v:o:r:l:h" opt; do
  case $opt in
    v) VOICE="$OPTARG" ;;
    o) OUTPUT="$OPTARG" ;;
    r) RATE="$OPTARG" ;;
    l) VOLUME="$OPTARG" ;;
    h)
      echo "用法: $0 [-v voice] [-o output] [-r rate] [-l volume] \"text\""
      echo "  默认语音: zh-CN-XiaoxiaoNeural (中文女声)"
      echo "  其他选项:"
      echo "    zh-CN-YunxiNeural   (中文男声)"
      echo "    zh-CN-YunyangNeural (中文青年男声)"
      echo "    zh-CN-XiaoyiNeural  (中文活力女声)"
      exit 0
      ;;
    *) echo "未知参数: -$OPTARG"; exit 1 ;;
  esac
done
shift $((OPTIND-1))

TEXT="${1:-}"
if [ -z "$TEXT" ]; then
  echo "错误: 请提供要朗读的文字"
  echo "用法: $0 [-v voice] \"要朗读的文字\""
  exit 1
fi

# 如果未指定输出路径，自动生成
if [ -z "$OUTPUT" ]; then
  TIMESTAMP=$(date +%Y%m%d_%H%M%S)
  OUTPUT="/tmp/tts_${TIMESTAMP}.mp3"
fi

echo "🔊 语音生成中..."
echo "   语音: $VOICE"
echo "   文字: ${TEXT:0:50}..."
echo "   输出: $OUTPUT"

edge-tts \
  --voice "$VOICE" \
  --text "$TEXT" \
  --write-media "$OUTPUT" \
  --rate "$RATE" \
  --volume "$VOLUME"

echo "✅ 完成: $OUTPUT ($(du -h "$OUTPUT" | cut -f1))"

# 可选：自动播放（需要 mpg123/ffplay）
# if command -v ffplay &>/dev/null; then
#   ffplay -nodisp -autoexit "$OUTPUT"
# elif command -v mpg123 &>/dev/null; then
#   mpg123 "$OUTPUT"
# fi
