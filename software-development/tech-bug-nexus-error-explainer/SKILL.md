---
name: tech-bug-nexus-error-explainer
description: "NEXUS Error Explainer - 付费AI错误解释服务。提交错误信息/堆栈跟踪，返回根因解释和修复建议。支持x402/MPP/Legacy三种支付方式，接受ADA/USDC/XLM等加密货币。"
tags: [错误解释, AI, 付费, NEXUS, API]
---

# NEXUS Error Explainer

付费AI错误解释服务。粘贴任意错误信息/堆栈跟踪或异常，即时获得根因解释和修复建议。

- 价格: $0.15/请求
- 接受: ADA, DJED, iUSD, USDCx, USDM (Cardano) | USDC, XLM (Stellar) | XRP, RLUSD (XRPL)
- 端点: https://ai-service-hub-15.emergent.host

## 使用方式

### Option A: x402 Standard（推荐）

```bash
# 1. 调用端点（不带支付头）
curl -X POST https://ai-service-hub-15.emergent.host/api/original-services/error-explain \
  -H "Content-Type: application/json" \
  -d '{"input": "你的错误信息"}'

# 2. 支付后重试
curl -X POST https://ai-service-hub-15.emergent.host/api/original-services/error-explain \
  -H "Content-Type: application/json" \
  -H "X-PAYMENT: <base64url JSON>" \
  -d '{"input": "你的错误信息"}'
```

### Option B: MPP Standard

```bash
curl -X POST https://ai-service-hub-15.emergent.host/api/original-services/error-explain \
  -H "Content-Type: application/json" \
  -H "Authorization: Payment <credential>" \
  -d '{"input": "你的错误信息"}'
```

### Option C: Legacy Header（免费测试用 sandbox_test）

```bash
curl -X POST https://ai-service-hub-15.emergent.host/api/original-services/error-explain \
  -H "Content-Type: application/json" \
  -H "X-Payment-Proof: sandbox_test" \
  -d '{"input": "Example error: Cannot read property of undefined"}'
```

## 支持网络

| 网络 | 资产 |
|------|------|
| Cardano mainnet | ADA, DJED, iUSD, USDCx, USDM |
| Stellar pubnet | USDC, XLM |
| XRPL | XRP, RLUSD |
| Sandbox（免费测试） | - |

## 辅助端点

| 用途 | 端点 |
|------|------|
| x402 服务发现 | GET /api/mpp/x402 |
| MPP 服务发现 | GET /api/mpp/discover |
| 稳定币注册 | GET /api/mpp/stablecoins |
| Stellar 信息 | GET /api/mpp/stellar |
| Gas 赞助 | POST /api/mpp/stellar/sponsor |

## 安全与隐私

- 所有数据通过 HTTPS/TLS 传输
- 请求处理后即丢弃，不持久存储
- 支付通过 Masumi Protocol 在 Cardano 链上验证
- 不访问文件系统或执行 Shell 命令
