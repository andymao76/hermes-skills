# 阿里云百炼 (Aliyun Bailian) Provider 配置指南

## 概述

阿里云百炼是阿里巴巴官方大模型服务平台，提供通义千问 (Qwen) 系列模型的 API 访问。

**适用场景:**
- 需要最新 Qwen3.5/Qwen3.7 系列模型
- 追求国内直连低延迟
- 需要企业级 SLA 和发票
- 利用免费额度 (每模型 100 万 tokens，90 天有效)

## API Key 获取流程

### 步骤 1: 登录控制台

访问：https://bailian.console.aliyun.com/cn-beijing?tab=model#/model-market

**地域选择:** 华北 2 (北京) ← 推荐，延迟最低

### 步骤 2: 创建 API Key

1. 点击右上角 **API Key** 进入管理页
2. 单击 **创建 API Key**
3. 配置:
   - **归属业务空间**: 默认
   - **权限**: 建议选 **全部** (或自定义 IP 白名单)
4. 单击 **确定**，复制 API Key (格式：`sk-xxxxx`)

**重要:**
- 需主账号 或 有 `管理员`/`API-Key` 权限的子账号
- 关闭弹窗后无法查看完整 Key，需立即保存
- 每地域最多创建 50 个 API Key

### 步骤 3: 配置到 Hermes

```bash
# 写入 .env (推荐，更安全)
echo 'DASHSCOPE_API_KEY=sk-xxx' >> ~/.hermes/.env

# 配置 provider
hermes config set providers.bailian.api_key sk-xxx
hermes config set providers.bailian.base_url https://dashscope.aliyuncs.com/compatible-mode/v1
hermes config set providers.bailian.default qwen-plus
```

## 完整配置示例

```yaml
# ~/.hermes/config.yaml
providers:
  bailian:
    api_key: sk-xxx  # 或从 DASHSCOPE_API_KEY 环境变量读取
    base_url: https://dashscope.aliyuncs.com/compatible-mode/v1
    default: qwen-plus
```

## 可用模型对比

| 模型 | 上下文 | 输入价 (¥/M) | 输出价 (¥/M) | 适用场景 |
|------|--------|-------------|-------------|----------|
| **qwen-plus** | 128K | 0.8 | 2.0 | 日常对话，性价比高 ✅ |
| **qwen3.5-plus** | 256K | 0.4 | 2.4 | 长文档，最便宜 |
| **qwen-max** | 32K | 2.4 | 9.6 | 复杂任务 (但 32K<64K 不满足 Hermes) ❌ |
| **qwen3-max** | 256K | 1.2 | 6.0 | 旗舰模型，能力强 ✅ |
| **qwen-turbo** | 128K | 更低 | 更低 | 极速响应 |

**注意:** `qwen-max` 只有 32K 上下文，低于 Hermes 最低要求 (64K)，会报错。

## 测试命令

```bash
# 临时测试
hermes chat -q "测试问题" --provider bailian --model qwen-plus

# 切换默认
hermes config set model.provider bailian
hermes config set model.model qwen-plus
```

## 实测数据 (2026-06-08)

**测试提示词:** "用 30 字左右介绍你自己，并说出现在的日期和时间"

| 提供商 | 模型 | 响应时间 | 回答质量 |
|--------|------|----------|----------|
| 阿里云百炼 | qwen-plus | **8 秒** ⚡ | 详细 (56 字)，含精确时间 |
| SiliconFlow | Qwen3.5-397B | **13 秒** | 简洁 (32 字)，仅日期 |

**结论:** 阿里云百炼响应快 60%，适合对延迟敏感的场景。

## 与 SiliconFlow 对比

| 维度 | 阿里云百炼 | SiliconFlow |
|------|-----------|-------------|
| **身份** | 官方原厂 (阿里) | 第三方聚合平台 |
| **模型新鲜度** | 最新 Qwen3.7 系列 ✅ | Qwen3.5/3.6 |
| **响应速度** | 8 秒 (国内直连) ⚡ | 13 秒 (国际站需代理) |
| **上下文** | 128K-256K | 全部 256K+ ✅ |
| **免费额度** | 每模型 100 万 (90 天) ✅ | 少量免费小模型 |
| **价格 (qwen-plus)** | ¥0.8/¥2.0 | N/A (无此模型) |
| **多模型支持** | 仅阿里系 | DeepSeek/GLM/Kimi 等 ✅ |
| **特色功能** | 思考模式切换、Batch 半价 | 统一 API，方便切换 |

## 推荐组合策略

**高强度开发期:**
1. 先用完阿里云百炼免费额度 (每模型 100 万 tokens)
2. 切换到 SiliconFlow 国内站 (长期稳定使用)
3. 复杂任务用 Qwen3-max，日常用 qwen-plus

**企业用户:**
- 阿里云百炼：稳定性 + 发票 + SLA
- 配置 IP 白名单提升安全性

**个人开发者:**
- SiliconFlow 国内站：性价比更高，模型选择多

## 常见问题

### Q: API Key 权限如何控制？
A: 华北 2 地域支持 IP 白名单。创建时选"自定义"权限，填入允许的 IP 地址。

### Q: 免费额度多久过期？
A: 开通后 90 天内有效，每个模型独立 100 万 tokens。

### Q: 如何查看用量？
A: 控制台 → 用量统计，或通过 `curl` 调用 API 查询。

### Q: 临时访问如何控制风险？
A: 使用临时 API Key (60 秒有效期)，通过 API 生成。

## 参考资料

- 百炼控制台：https://bailian.console.aliyun.com
- API Key 管理：https://help.aliyun.com/zh/model-studio/model-pricing
- 模型价格：https://help.aliyun.com/zh/model-studio/model-pricing
- 错误码：https://help.aliyun.com/zh/model-studio/error-code