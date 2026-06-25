# 三层架构路由配置 (v3.5)

## 硬件拓扑

```
Win11 (控制层)
  Hermes Agent 原生运行 (非 WSL)
  Provider: deepseek (云) / gem12_local/gem12_fast (本地 eGPU)
  多平台: Feishu/WhatsApp/Telegram/Discord
      │ API / MCP
GEM12+ 8845HS (调度层)
  ChromaDB 向量数据库
  RAG Pipeline + Embedding
  Intent Router + Policy Engine
  MCP Server + cron 调度
  → 不跑大模型，只做智能中枢
      │ OCuLink PCIe x4 (64Gbps)
RTX 4060 Ti 16GB (推理层)
  Ollama / llama.cpp / vLLM
  Qwen2.5 14B (主力) / 7B (快速) / DeepSeek 14B (推理)
  CUDA 加速 · 160W TDP · 20-90 tok/s
```

## 三层路由规则

| 数据级别 | 路径 | 响应速度 | 脱网可用 |
|---------|------|---------|:--------:|
| PUBLIC | Win11 → DeepSeek API | 50+ tok/s | ❌ |
| PRIVATE | Win11 → GEM12+ RAG → 4060Ti | 40-60 tok/s (14B) / 70-90 tok/s (7B) | ✅ |
| HIGH_SENSITIVE | Win11 → GEM12+ RAG → 4060Ti (强制) | 同 PRIVATE | ✅ |

## Provider 配置示例 (Hermes config.yaml)

```yaml
providers:
  deepseek:
    base_url: https://api.deepseek.com/v1
    default: deepseek-v4-flash
    # 公有知识路径

  gem12_local:
    base_url: http://GEM12_IP:8080/v1
    default: qwen2.5:14b
    # 私有推理路径 (主力)

  gem12_fast:
    base_url: http://GEM12_IP:8081/v1
    default: qwen2.5:7b
    # 快速响应路径

  gem12_reasoning:
    base_url: http://GEM12_IP:8082/v1
    default: deepseek-r1:14b
    # 复杂推理路径
```

## GEM12+ 所需软件栈

| 组件 | 版本/路径 | 端口 |
|------|----------|:----:|
| Ollama (主推理引擎) | 最新 | 11434 |
| ChromaDB (向量数据库) | pip install chromadb | — |
| FastAPI (RAG查询服务) | pip install fastapi uvicorn | 8800 |
| MCP Server | npm/hermes | 自定义 |
| Nomic Embed (嵌入模型) | ollama pull nomic-embed-text | — |

## 关键配置命令

```bash
# Ollama 显存保护 (16GB 4060Ti)
sudo systemctl edit ollama.service
# 添加:
# [Service]
# Environment='OLLAMA_MAX_LOADED_MODELS=1'
# Environment='OLLAMA_NUM_PARALLEL=2'

# RAG 服务启动
uvicorn rag_server:app --host 0.0.0.0 --port 8800

# 知识库索引
python3 index_knowledge.py /home/knowledge/li/
python3 index_knowledge.py /home/knowledge/customers/
```

## 模型推荐

| 模型 | 量化 | 显存 | tok/s | 角色 |
|------|:----:|:----:|:-----:|------|
| Qwen2.5 14B | Q4_K_M | ~9GB | 40-60 | 主推理 (LI/编程/协议) |
| Qwen2.5 7B | Q4_K_M | ~4.5GB | 70-90 | 快速响应 |
| DeepSeek 14B | Q4_K_M | ~9GB | 35-55 | 复杂推理 |
| Llama 3 8B | Q4_K_M | ~5.5GB | 60-80 | 英文任务 |
| Nomic Embed | FP32 | <1GB | — | RAG 嵌入 |
