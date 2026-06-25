#!/bin/bash
# audit-secret-scanner.sh — 扫描硬编码密钥和密码
echo "=== Secret Scanner ==="

# AWS Access Key
grep -rn 'AKIA[0-9A-Z]\{16\}' \
  --include='*.{js,ts,py,go,java,rb,env,yml,yaml,json,xml,cfg,conf,ini,toml,sh}' \
  ~/knowledge/ ~/skills/ 2>/dev/null | grep -v 'node_modules\|\.git\|vendor\|__pycache__' \
  && echo "⚠️  发现 AWS Key" || echo "✅ AWS Key 扫描通过"

# 通用 API Key / Token
grep -rn -i 'api[_-]\?key\|api[_-]\?secret\|access[_-]\?token\|auth[_-]\?token\|bearer ' \
  --include='*.{js,ts,py,go,java,rb,env,yml,yaml,json,xml}' \
  ~/knowledge/ ~/skills/ 2>/dev/null | grep -v 'node_modules\|\.git\|example\|test\|mock\|placeholder\|xxxx' \
  && echo "⚠️  发现 API 密钥" || echo "✅ API 密钥扫描通过"

# 私钥文件
find ~/ -name '*.pem' -o -name '*.key' -o -name '*.p12' -o -name 'id_rsa' -o -name 'id_ed25519' \
  -not -path '*/.git/*' -not -path '*/node_modules/*' 2>/dev/null \
  | while read f; do echo "⚠️  发现私钥文件: $f"; done

# 环境变量中的硬编码密码
grep -rn -i 'password\s*[:=]\s*["'\''"'\''][^"'\''"'\'']*["'\''"'\'']' \
  --include='*.{env,yml,yaml,json,xml,cfg,conf,ini,toml}' \
  ~/knowledge/ ~/skills/ 2>/dev/null | grep -v 'example\|test\|mock\|placeholder\|changeme\|xxxx' \
  && echo "⚠️  发现硬编码密码" || echo "✅ 密码扫描通过"

# OpenAI / Anthropic API Key 格式
grep -rn 'sk-[A-Za-z0-9]\{20,\}' \
  --include='*.{js,ts,py,go,java,rb,env,yml,yaml,json,xml,cfg,conf,ini,toml,sh}' \
  ~/knowledge/ ~/skills/ 2>/dev/null | grep -v 'node_modules\|\.git\|vendor' \
  && echo "⚠️  发现 LLM API Key" || echo "✅ LLM API Key 扫描通过"
