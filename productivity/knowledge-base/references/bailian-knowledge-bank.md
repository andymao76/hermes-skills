# 阿里云百炼 (Bailian) 知识库索引

> 已摄入文件列表（~/knowledge/）

| 文件 | 内容 |
|------|------|
| 阿里云百炼_平台手册.md | 平台定位、模型体系、API 接入、应用构建、计费 |

## 本机配置

| 项目 | 值 |
|------|-----|
| Provider | bailian (config.yaml) |
| API Key | DASHSCOPE_API_KEY (~/.hermes/.env) |
| Base URL | ws-cvcdp75lzuizyly0.cn-beijing.maas.aliyuncs.com/compatible-mode/v1 |
| 默认模型 | qwen-plus |
| 地域 | 华北2（北京） |
| 工作空间 | ws-cvcdp75lzuizyly0（默认业务空间） |
| 限流 | 30,000 RPM / 5,000,000 TPM |

## 关键要点

- 四地域独立：北京(dashscope.aliyuncs.com) / 新加坡 / 美国 / 德国，API Key 不通用
- 千问旗舰：max(最强) > plus(推荐，0.8元/百万输入) > flash(便宜) > turbo
- 思考模式输出贵 4 倍（非思考 2元 vs 思考 8元/百万token）
- 阶梯计费：按单次请求输入 token 总量分档
- 新人免费额度 90 天，仅北京地域，用完默认继续扣费
- Batch API 半价，不限流
- 上下文缓存折扣
