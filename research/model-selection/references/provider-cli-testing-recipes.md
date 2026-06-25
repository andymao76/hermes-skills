# Provider 切换与测试 CLI 速查

## 一键测试命令 (copy-paste ready)

### 连通性测试 (所有提供商)

```bash
# SiliconFlow 国际站
hermes chat -q "用 10 字回答你现在是什么模型" --provider siliconflow -Q

# SiliconFlow 国内站 (需先配置)
hermes chat -q "用 10 字回答你现在是什么模型" --provider siliconflow-cn -Q

# 阿里云百炼
hermes chat -q "用 10 字回答你现在是什么模型" --provider bailian --model qwen-plus -Q

# DeepSeek
hermes chat -q "用 10 字回答你现在是什么模型" --provider deepseek -Q
```

### latency 测试 (curl 直接测 API)

```bash
# 创建格式化模板
cat > /tmp/curl-format.txt << 'EOF'
time_namelookup:  %{time_namelookup}s
   time_connect:  %{time_connect}s
time_appstart:  %{time_appconnect}s
  time_pretransfer:  %{time_pretransfer}s
     time_redirect:  %{time_redirect}s
time_starttransfer:  %{time_starttransfer}s
----------
     time_total:  %{time_total}s
----------
     speed_download:  %{speed_download}
EOF

# 测试各端点
curl -w "@/tmp/curl-format.txt" -o /dev/null -s "https://api.siliconflow.cn/v1"
curl -w "@/tmp/curl-format.txt" -o /dev/null -s "https://api.siliconflow.com/v1" -x 127.0.0.1:7897
curl -w "@/tmp/curl-format.txt" -o /dev/null -s "https://dashscope.aliyuncs.com/compatible-mode/v1"
```

### 响应时间对比 (并行执行)

```bash
# 同时跑三个提供商，对比总耗时
time hermes chat -q "用 30 字介绍你自己" --provider siliconflow --model "Qwen/Qwen3.5-397B-A17B" -Q &
time hermes chat -q "用 30 字介绍你自己" --provider siliconflow-cn --model "Qwen/Qwen3.5-397B-A17B" -Q &
time hermes chat -q "用 30 字介绍你自己" --provider bailian --model qwen-plus -Q &
wait
```

### 切换默认 Provider

```bash
# 临时切换 (仅当前对话)
hermes chat -q "问题" --provider bailian --model qwen-plus

# 永久切换 (修改 config.yaml)
hermes config set model.provider bailian
hermes config set model.model qwen-plus

# 验证
hermes config get model.provider
hermes config get model.model
```

## 常见 Provider 配置命令

### SiliconFlow 国内站 (新增配置)

```bash
hermes config set providers.siliconflow-cn.api_key sk-xxx
hermes config set providers.siliconflow-cn.base_url https://api.siliconflow.cn/v1
hermes config set providers.siliconflow-cn.default "Qwen/Qwen3.5-397B-A17B"
```

### 阿里云百炼 (新增配置)

```bash
hermes config set providers.bailian.api_key sk-xxx
hermes config set providers.bailian.base_url https://dashscope.aliyuncs.com/compatible-mode/v1
hermes config set providers.bailian.default qwen-plus
```

### DeepSeek

```bash
hermes config set providers.deepseek.api_key sk-xxx
hermes config set providers.deepseek.base_url https://api.deepseek.com/v1
hermes config set providers.deepseek.default deepseek-v4-pro
```

## 环境变量配置 (.env)

```bash
# API Keys 统一存储在 ~/.hermes/.env
echo 'DASHSCOPE_API_KEY=sk-xxx' >> ~/.hermes/.env
echo 'SILICONFLOW_API_KEY=sk-xxx' >> ~/.hermes/.env
echo 'DEEPSEEK_API_KEY=sk-xxx' >> ~/.hermes/.env

# 重载环境变量 (或重启 terminal)
source ~/.hermes/.env
```

## 快速对比表

| Provider | 模型 | 响应时间 | 延迟 | 上下文 | 价格 (¥/M) |
|----------|------|----------|------|--------|-----------|
| bailian | qwen-plus | 8s | ~150ms | 128K | 0.8 / 2.0 |
| siliconflow-cn | Qwen3.5-397B | ~5s (预估) | ~100ms | 256K | 2.0 / 1.2 |
| siliconflow | Qwen3.5-397B | 13s | ~1000ms | 256K | 2.0 / 1.2 |
| deepseek | deepseek-v4-pro | 9s | - | 1M | - |

## 故障排查

### API Key 无效 (401)

```bash
# 检查 API Key 是否正确配置
hermes config get providers.bailian.api_key

# 检查环境变量
echo $DASHSCOPE_API_KEY

# 重新配置
hermes config set providers.bailian.api_key sk-xxx
```

### 代理连接失败

```bash
# 检查代理是否运行
curl -I http://127.0.0.1:7897

# 检查 config.yaml 中是否正确设置
hermes config get proxy

# 对于 SiliconFlow 国际站，必须启用代理
```

### 模型不支持 (400)

```bash
# 检查模型 ID 格式
hermes config get providers.siliconflow.default
# 正确格式：Qwen/Qwen3.5-397B-A17B
# 错误格式：Qwen3.5-397B

# 查看 provider 支持的模型
# (需要调用 models API 或查看官网文档)
```