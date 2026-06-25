# SiliconFlow 国内站 vs 国际站 对比

## 核心结论

**API 完全兼容，仅需改动 Base URL**。两个站使用同一套 API 格式、模型命名、SDK。

## 网络性能对比

| 站点 | API 端点 | 延迟 | 网络路径 | 速度比 |
|------|----------|------|----------|--------|
| **国内站** | `api.siliconflow.cn` | **~100ms** ⚡ | 国内直连 | **11 倍快** |
| **国际站** | `api.siliconflow.com` | **~1000ms** 🐢 | 代理转发 (127.0.0.1:7897) | 基准 |

**实测数据 (2026-06-08):**
- 国内站：`curl` 延迟 0.09s
- 国际站：`curl --proxy` 延迟 1.02s

## 功能对比表

| 维度 | 国内站 (.cn) | 国际站 (.com) |
|------|-------------|--------------|
| **域名** | `siliconflow.cn` | `siliconflow.com` |
| **API Base URL** | `https://api.siliconflow.cn/v1` | `https://api.siliconflow.com/v1` |
| **网络要求** | ✅ 国内直连 | ❌ 需代理/科学上网 |
| **响应延迟** | ~100ms | ~1000ms+ |
| **免费额度** | 新用户 14 元 (约 2 千万 tokens) | $1 美元体验金 |
| **计费货币** | 人民币 (¥) | 美元 ($) |
| **模型覆盖** | 主流开源模型 (DeepSeek/Qwen/GLM/Kimi) | 更全 (含部分国际独有模型) |
| **发票支持** | ✅ 增值税专票 | ❌ 不支持 |
| **支付方式** | 微信/支付宝/对公转账 | 信用卡/PayPal |
| **账号体系** | 独立 (余额不互通) | 独立 (余额不互通) |

## Hermes 配置示例

### 配置两个 provider (共存)

```yaml
providers:
  # 国际站 (当前默认)
  siliconflow:
    api_key: sk-yb...etvn
    base_url: https://api.siliconflow.com/v1
    default: Qwen/Qwen3.5-397B-A17B

  # 国内站 (新增)
  siliconflow-cn:
    api_key: sk-xxx  # 需单独注册获取
    base_url: https://api.siliconflow.cn/v1
    default: Qwen/Qwen3.5-397B-A17B
```

### 切换命令

```bash
# 临时使用国内站
hermes chat -q "问题" --provider siliconflow-cn

# 或切换默认 provider
hermes config set model.provider siliconflow-cn
```

## 迁移步骤

1. **注册国内站账号**: https://cloud.siliconflow.cn/
2. **获取 API Key**: 个人中心 → API Key
3. **修改配置**: 仅改动 `base_url` 和 `api_key`
4. **验证**: `hermes chat -q "测试" --provider siliconflow-cn`

**其他一切不变:**
- ✅ 模型 ID 相同 (`Qwen/Qwen3.5-397B-A17B`)
- ✅ 请求格式相同 (`/v1/chat/completions`)
- ✅ SDK 代码相同
- ✅ Token 计费逻辑相同

## 切换建议

**强烈推荐切换到国内站，如果:**
- ✅ 你在中国大陆，受 GFW 限制
- ✅ 你追求更快响应速度 (11 倍提升)
- ✅ 你需要人民币发票报销
- ✅ 你尚未在国际站充值大量余额

**保持国际站，如果:**
- ⚠️ 你需要国际站独有的模型
- ⚠️ 你已有国际站大额余额 (无法转移)
- ⚠️ 你需要美元支付/国际发票

## 预期性能提升

| 操作类型 | 国际站耗时 | 国内站预测 | 提升 |
|----------|-----------|-----------|------|
| 简单对话 | ~13 秒 | ~3-5 秒 | 60%+ |
| 长文档分析 | ~30 秒+ | ~10-15 秒 | 50%+ |
| 代码生成 | ~20 秒 | ~8-10 秒 | 50%+ |

## 参考资料

- SiliconFlow 国内官网：https://siliconflow.cn
- SiliconFlow 国际官网：https://siliconflow.com
- 国内站定价：https://siliconflow.cn/pricing