# Ollama 模型兼容性验证方法

验证一个 Ollama 模型是否能作为 Hermes Agent 主模型的标准化流程。

## 一、检查工具调用支持（`tools` capability）

```bash
curl -s http://<ollama_host>:11434/api/tags \
  | python3 -c "import sys,json; data=json.load(sys.stdin)
for m in data['models']:
    name = m['name']
    caps = m.get('capabilities', [])
    ctx = m['details'].get('context_length', '?')
    print(f'{name:30s} ctx={ctx:>7} tools={\"tools\" in caps}")
"
```

Hermes 主模型必须包含 `tools` 能力，否则无法进行函数调用。

## 二、检查 `content` 字段是否正常（Qwen3 检查）

```bash
# Qwen3 模型的问题：回复进入 reasoning 字段，content 为空
curl -s -X POST http://<ollama_host>:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"<model_name>","messages":[{"role":"user","content":"say hi in 3 words"}],"max_tokens":50,"stream":false}' \
  | python3 -c "
import sys, json
d = json.load(sys.stdin)
msg = d['choices'][0]['message']
content = msg.get('content','')
reasoning = msg.get('reasoning','')
print('content: ', repr(content[:100]))
print('reasoning:', repr(reasoning[:100]) if reasoning else '(empty)')
if content.strip():
    print('✅ content 正常 → 可做主模型')
elif reasoning.strip():
    print('❌ reasoning 才有内容，content 为空 → 不能做主模型')
else:
    print('❌ 无任何回复')
"
```

**测试结果（本机 Ollama 192.168.250.83:11434）：**

| 模型 | content | reasoning | 能否做主模型 |
|:-----|:--------|:----------|:------------|
| qwen2.5:7b | `"Hello there!"` | (empty) | ✅ |
| qwen2.5-coder:7b | `"Hi there!..."` | (empty) | ✅ |
| qwen2.5-7b-64k:latest | 正常 | (empty) | ✅ |
| **qwen3:8b** | `""` | **有内容** | **❌ 不能** |
| **qwen3:14b** | `""` | **有内容** | **❌ 不能** |
| deepseek-r1:7b | `""` | 有内容 | ❌ 且无 tools 支持 |

**已知原因：** Qwen3 系列（qwen3:8b/14b/32b）在 Ollama 的 OpenAI 兼容 API 中，将 thinking 阶段的内容单独放入 `reasoning` 字段，但最终回复没有汇总回 `content` 字段。Hermes Agent 从 `content` 读取回复，因此 Qwen3 全系不适合作为主模型。

## 三、检查 context_length

```bash
curl -s http://<ollama_host>:11434/api/show -d '{"name":"<model_name>"}' \
  | python3 -c "
import sys, json
d = json.load(sys.stdin)
for k, v in d.get('model_info', {}).items():
    if 'context_length' in k:
        print(f'{k} = {v}')
"
```

Hermes 要求 `MINIMUM_CONTEXT_LENGTH = 64_000`。如果模型报告的 context_length < 64K，需要强制覆写：

```bash
hermes config set model.ollama_num_ctx 65536
hermes config set model.context_length 65536
```

## 四、完整一键验证

```bash
# 验证所有模型的 tools 支持 + content 字段
curl -s http://<ollama_host>:11434/api/tags | python3 -c "
import sys, json, subprocess, urllib.request

data = json.load(sys.stdin)
for m in data['models']:
    name = m['name']
    caps = m.get('capabilities', [])
    ctx = m['details'].get('context_length', '?')
    has_tools = 'tools' in caps
    
    # 验证 content 字段
    payload = json.dumps({
        'model': name,
        'messages': [{'role': 'user', 'content': 'say hi in 3 words'}],
        'max_tokens': 50,
        'stream': False
    }).encode()
    
    content_ok = '?'
    try:
        req = urllib.request.Request(
            f'http://{sys.argv[1] if len(sys.argv)>1 else \"192.168.250.83:11434\"}/v1/chat/completions',
            data=payload,
            headers={'Content-Type': 'application/json'}
        )
        resp = json.loads(urllib.request.urlopen(req, timeout=30).read())
        msg = resp['choices'][0]['message']
        c = msg.get('content', '').strip()
        r = msg.get('reasoning', '').strip()
        if c: content_ok = '✅ content'
        elif r: content_ok = '⚠️ reasoning only'
        else: content_ok = '❌ empty'
    except Exception as e:
        content_ok = f'❌ {str(e)[:30]}'
    
    print(f'{name:30s} ctx={str(ctx):>7} tools={has_tools}  {content_ok}')
" 192.168.250.83:11434
```
