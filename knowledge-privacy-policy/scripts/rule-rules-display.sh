#!/bin/bash
# ==============================================================================
# RULE 规则启动显示脚本 — 供 shell hook 使用
# 
# 用途：在 Hermes 启动时显示用户定义的 RULE 规则列表
# 
# 配置方式（在 ~/.hermes/config.yaml 的 hooks: 段）：
#
#   hooks:
#     on_session_start:
#       - command: "~/.hermes/skills/knowledge-privacy-policy/scripts/role-rules-display.sh"
#         timeout: 5
#
# 注意：on_session_start hook 无法通过 stdout 注入上下文，
# 该脚本主要用于记录到日志作为审计依据。
# CLI 模式下仍需 Agent 在每条新会话第一条消息主动展示规则。
# ==============================================================================

cat << 'RULE_BANNER'
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚙️  Hermes Agent  RULE 规则清单（启动自检）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

RULE1  — 工作/项目问题先查本地知识库、技能库、笔记，无结果再上网搜
RULE5  — 搜索结果标注出处（URL/文章名/来源），维基百科优先英文版
RULE6  — 知识隔离：公开技术可发LLM，LI/LIG/HW/ZTE/NSN/Ericsson/ZTLIG/
         OWLS/SICMS/SECPASS 不进 Prompt，待私有 LLM。作者名保留原文
RULE7  — 每次启动时先显示所有 RULE 规则列表和详细说明
RULE8  — 网上搜索来源务必标注出处（URL/来源/文章名）供人工核验
RULE9  — 源码安全隔离：~/work-projects/ 下 LI 领域项目源码（HI/HI2/HI3/
         X1/X2/X3 编解码算法等）严格禁止发送到 Web 或在线 LLM 处理，
         仅限本地文件/终端操作
RULE10 — 数据治理优先：调用外部 LLM 前必须遵守
         knowledge/_system/security/llm_data_governance.skill.md
         每日 08:30 自动安全审计
RULE11 — 百度网盘下载文档需经安全审计分类后使用：LI/项目→li/
         客户→customers/，密码密钥→secrets/，分类前不得RAG检索

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

数据分类速查：
  公开知识  /public/  /telecom/  /bigdata/  /hermes/     → ✅ 可发送
  内部经验  /internal/                                    → ⚠️ 脱敏后发
  客户数据  /customers/                                   → ❌ 禁止发送
  敏感数据  /secrets/                                     → 🔥 绝对禁止
  LI数据    /li/                                          → 🔴 绝对禁止
  LI源码    ~/work-projects/ETSI-ASN1-Assistant/ 等       → 🔴 绝对禁止

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RULE_BANNER
