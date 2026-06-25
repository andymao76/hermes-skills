# 腾讯云 MCP Server 家族参考

**来源**: 腾讯云开发者社区 (2026-06-14)
**适用场景**: 用户需要通过AI管理腾讯云资源时

## 四款 MCP Server

### 1. CVM MCP Server（云服务器）
**功能**: 全生命周期管理（创建/变配/开关机/重装系统）
**安装**: `pip install mcp-server-cvm` (需要 uv)
**配置**:
```json
{
  "mcpServers": {
    "tencent-cvm": {
      "command": "uv",
      "args": ["run", "mcp-server-cvm"],
      "env": {
        "TENCENTCLOUD_SECRET_ID": "YOUR_SECRET_ID",
        "TENCENTCLOUD_SECRET_KEY": "YOUR_SECRET_KEY",
        "TENCENTCLOUD_REGION": "YOUR_REGION"
      }
    }
  }
}
```

### 2. Lighthouse MCP Server（轻量应用服务器）
**功能**: 健康检测、故障诊断、防火墙管理
**安装**: `npm i lighthouse-mcp-server`
**配置**:
```json
{
  "mcpServers": {
    "lighthouse-mcp-server": {
      "command": "npx",
      "args": ["-y", "lighthouse-mcp-server"],
      "env": {
        "TENCENTCLOUD_SECRET_KEY": "YOUR_SECRET_KEY",
        "TENCENTCLOUD_SECRET_ID": "YOUR_SECRET_ID"
      }
    }
  }
}
```
**典型用例**: "帮我检查一下服务器为什么没法登录"、"帮我放通防火墙规则"

### 3. HAI MCP Server（高性能应用服务）
**功能**: 一键部署AI应用（DeepSeek等）
**安装**: `pip install mcp-server-hai`
**配置**: 同CVM格式

### 4. TAT MCP Server（自动化助手）
**功能**: 远程在服务器内执行命令（无需SSH）
**安装**: `pip install mcp-server-tat`
**配置**: 同CVM格式
**典型用例**: "帮我部署Nginx"、"帮我更新SSL证书"

## 前提条件

- 腾讯云 API 密钥（SecretId + SecretKey）
- Python + uv（CVM/HAI/TAT）
- Node.js + npm（Lighthouse）

## 用户环境备注

- 用户服务器: 腾讯云轻量应用服务器 (Lighthouse), 实例 ins-lb39a1an
- 用户状态: 2026-06-14 表示"暂时不要"安装，需要时再配置
- 用户无 IDA Pro，逆向工程需求可用 Ghidra 替代

## 参考链接

- 腾讯云 MCP Server 介绍: https://cloud.tencent.com/developer/article/2513043
- CVM MCP: https://cloud.tencent.com/developer/mcp/server/10047
- Lighthouse MCP: npm package lighthouse-mcp-server
- HAI MCP: pip package mcp-server-hai
- TAT MCP: pip package mcp-server-tat
