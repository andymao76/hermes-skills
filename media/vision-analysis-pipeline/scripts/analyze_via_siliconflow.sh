#!/usr/bin/env bash
# analyze_via_siliconflow.sh
# Fallback image analyzer when the active Hermes model lacks vision support.
# Uses SiliconFlow Qwen3-VL-8B-Instruct with auto-fallback:
#   1st try: CN endpoint (api.siliconflow.cn, direct)
#   2nd try: International endpoint (api.siliconflow.com, via proxy 7897)
#
# Usage:
#   ./analyze_via_siliconflow.sh <image_path> [question]
#
# If question is omitted, defaults to a generic description request.
#
# Example:
#   ./analyze_via_siliconflow.sh /home/andymao/temp-picture/screenshot.png \
#     "请详细描述这张截图，包括所有文字、图表和界面元素"

set -euo pipefail

IMAGE_PATH="${1:?Usage: $0 <image_path> [question]}"
QUESTION="${2:-请详细描述这张图片的内容，包括所有可见的文字、图表、界面元素和数据}"

if ! [ -f "$IMAGE_PATH" ]; then
  echo "File not found: $IMAGE_PATH" >&2
  exit 1
fi

# Extract both API keys from config
SF_CN_KEY=$(python3 -c "
import yaml
with open('/home/andymao/.hermes/config.yaml') as f:
    c = yaml.safe_load(f)
print(c['providers']['siliconflow-cn']['api_key'])
")

SF_INTL_KEY=$(python3 -c "
import yaml
with open('/home/andymao/.hermes/config.yaml') as f:
    c = yaml.safe_load(f)
print(c['providers']['siliconflow']['api_key'])
")

# Base64 encode the image
B64=$(base64 -w0 "$IMAGE_PATH")
DATA_URL="data:image/jpeg;base64,${B64}"

# Build JSON payload into a temp file
TMPFILE=$(mktemp /tmp/sf_vlm_XXXXXX.json)
trap 'rm -f "$TMPFILE"' EXIT

# Escape question for shell-single-quote context
ESCAPED_Q=$(echo "$QUESTION" | sed "s/'/'\\\\''/g")

python3 -c "
import json
payload = {
    'model': 'Qwen/Qwen3-VL-8B-Instruct',
    'messages': [{
        'role': 'user',
        'content': [
            {'type': 'image_url', 'image_url': {'url': '$DATA_URL'}},
            {'type': 'text', 'text': '${ESCAPED_Q}'}
        ]
    }],
    'max_tokens': 1024,
    'temperature': 0.1
}
with open('$TMPFILE', 'w') as f:
    json.dump(payload, f)
"

echo "Analyzing: $(basename "$IMAGE_PATH") ($(du -h "$IMAGE_PATH" | cut -f1))"

# ---------- Try 1: CN endpoint (direct, no proxy) ----------
echo "→ Try 1: CN endpoint (api.siliconflow.cn)"
RESP=$(curl -s --max-time 60 \
  https://api.siliconflow.cn/v1/chat/completions \
  -H "Authorization: Bearer $SF_CN_KEY" \
  -H "Content-Type: application/json" \
  -d @"$TMPFILE" 2>&1) || true

# Check if curl timed out or returned an error
if echo "$RESP" | python3 -c "import sys; d=__import__('json').load(sys.stdin); assert 'choices' in d" 2>/dev/null; then
  # Success
  python3 -c "
import json, sys
data = json.loads('''$RESP''')
print(data['choices'][0]['message']['content'])
u = data.get('usage', {})
print(f\"[Tokens: prompt={u.get('prompt_tokens','?')}, completion={u.get('completion_tokens','?')}, endpoint=CN]\")
" 2>/dev/null || echo "$RESP" | python3 -c "
import json, sys
d = json.load(sys.stdin)
if 'choices' in d:
    print(d['choices'][0]['message']['content'])
elif 'error' in d:
    print(f'CN API Error: {d[\"error\"]}')
"
  exit 0
fi

echo "   ⚠ CN attempt failed or timed out, trying intl endpoint..."

# ---------- Try 2: International endpoint (via proxy) ----------
echo "→ Try 2: Intl endpoint (api.siliconflow.com via :7897)"
RESP2=$(curl -s --max-time 120 \
  --proxy http://127.0.0.1:7897 \
  https://api.siliconflow.com/v1/chat/completions \
  -H "Authorization: Bearer $SF_INTL_KEY" \
  -H "Content-Type: application/json" \
  -d @"$TMPFILE" 2>&1) || true

python3 -c "
import json, sys
try:
    data = json.loads('''$RESP2''')
    if 'choices' in data:
        print(data['choices'][0]['message']['content'])
        u = data.get('usage', {})
        print(f'[Tokens: prompt={u.get(\"prompt_tokens\",\"?\")}, completion={u.get(\"completion_tokens\",\"?\")}, endpoint=INTL]')
    elif 'error' in data:
        print(f'INTL API Error: {data[\"error\"].get(\"message\", data[\"error\"])}')
    else:
        print(json.dumps(data, indent=2)[:500])
except json.JSONDecodeError as e:
    print(f'JSON Parse Error (INTL): {e}')
    print(f'Raw response (first 500): ${RESP2:0:500}')
"