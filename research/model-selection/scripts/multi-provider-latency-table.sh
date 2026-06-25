#!/bin/bash
# 多 Provider 大模型连通性 & 时延表格化测试
# 用法: bash scripts/multi-provider-latency-table.sh
# 自动从 config.yaml 和 .env 读取 API keys

set -e

# 读取所有密钥
DEEPSEEK_KEY=$(grep -A3 '^  deepseek:' ~/.hermes/config.yaml | grep 'api_key:' | head -1 | sed 's/.*api_key: //')
SF_KEY=$(grep -A3 '^  siliconflow:' ~/.hermes/config.yaml | grep 'api_key:' | head -1 | sed 's/.*api_key: //')
SF_CN_KEY=$(grep -A3 '^  siliconflow-cn:' ~/.hermes/config.yaml | grep 'api_key:' | head -1 | sed 's/.*api_key: //')
BL_KEY=$(grep -A3 '^  bailian:' ~/.hermes/config.yaml | grep 'api_key:' | head -1 | sed 's/.*api_key: //')
GEMINI_KEY=$(grep GEMINI_API_KEY ~/.hermes/.env | head -1 | cut -d= -f2- | tr -d '"' | tr -d "'")

test_one() {
    local name="$1" provider="$2" model="$3" url="$4" key="$5" proxy="$6"
    local px=""
    [ "$proxy" = "1" ] && px="-x http://127.0.0.1:7897"
    
    local mt=30
    # 推理模型需要更大的 max_tokens，否则 content 为空
    [[ "$model" == *"v4"* ]] && mt=100
    
    local resp=$(curl -s -w $'\n%{http_code}\n%{time_total}' --max-time 30 $px \
        -H "Authorization: Bearer *** \
        -H "Content-Type: application/json" \
        -d "{\"model\":\"$model\",\"messages\":[{\"role\":\"user\",\"content\":\"hi\"}],\"max_tokens\":$mt}" \
        "$url" 2>/dev/null)
    
    local lines=()
    while IFS= read -r line; do lines+=("$line"); done <<< "$resp"
    local total=${#lines[@]}
    local http_code="${lines[$((total-2))]}"
    local time_val="${lines[$((total-1))]}"
    
    local body=""
    for ((i=0; i<total-2; i++)); do body+="${lines[$i]}"$'\n'; done
    
    local latency_ms=$(echo "$time_val * 1000" | bc 2>/dev/null | cut -d. -f1)
    [ -z "$latency_ms" ] && latency_ms="-"
    
    local content=$(echo "$body" | python3 -c "
import sys,json
d=json.load(sys.stdin)
if 'choices' in d and d['choices']:
    m=d['choices'][0].get('message',{})
    c=m.get('content','') or m.get('reasoning_content','') or '(ok)'
    print(c[:20])
elif 'error' in d:
    print('ERR:'+d['error'].get('message','')[:20])
else:
    print('UNKNOWN')
" 2>/dev/null)
    
    local status_icon status_color status_text
    if [ "$http_code" = "000" ]; then
        status_icon="❌"
        status_color="31"
        status_text="不可达"
    elif [[ "$content" == ERR:* ]]; then
        status_icon="❌"
        status_color="31"
        status_text="错误"
    elif [ -n "$content" ] && [[ "$content" != UNKNOWN ]]; then
        status_icon="✅"
        status_color="32"
        status_text="正常"
    else
        status_icon="⚠️"
        status_color="33"
        status_text="异常"
    fi
    
    printf "│ \033[${status_color}m%-24s\033[0m  │ %-12s │ %-26s │ \033[${status_color}m%-6s\033[0m │ %6s ms │\n" \
        "$name" "$provider" "$model" "$status_icon $status_text" "$latency_ms"
}

echo "╔══════════════════════════════════╦══════════════╦════════════════════════════════╦════════╦══════════╗"
echo "║ 名称                              ║ 提供商        ║ 模型                           ║ 状态    ║ 时延     ║"
echo "╠══════════════════════════════════╬══════════════╬════════════════════════════════╬════════╬══════════╣"

test_one "DeepSeek V4 Pro (主)"    "deepseek"       "deepseek-v4-pro"            "https://api.deepseek.com/v1/chat/completions"                       "$DEEPSEEK_KEY" "0"
test_one "DeepSeek V3 (SF国际)"    "siliconflow"    "deepseek-ai/DeepSeek-V3"     "https://api.siliconflow.com/v1/chat/completions"                    "$SF_KEY"       "1"
test_one "Qwen3.5 397B (SF国内)"   "siliconflow-cn" "Qwen/Qwen3.5-397B-A17B"      "https://api.siliconflow.cn/v1/chat/completions"                     "$SF_CN_KEY"    "1"
test_one "Qwen-Plus (百炼)"        "bailian"        "qwen-plus"                  "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions" "$BL_KEY"       "1"
test_one "Gemini 2.5 Flash"        "gemini"         "gemini-2.5-flash"           "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions" "$GEMINI_KEY" "0"

echo "╚══════════════════════════════════╩══════════════╩════════════════════════════════╩════════╩══════════╝"
echo ""
echo "注: deepseek-v4-pro 是推理模型，用 max_tokens=100 测试"
