# Enzyme 语义索引刷新指南

## 背景

Enzyme 是知识库的语义搜索引擎，基于嵌入向量 + 催化剂（catalyst）机制。知识库文件变更后需刷新索引才能被搜索到。

## 刷新命令

### 方法一：使用脚本（推荐，简单）
```bash
cd ~/knowledge && bash ~/.hermes/scripts/enzyme-init.sh
```

⚠️ **已知问题**：该脚本带有 `set -e`，当 `source ~/.hermes/.env` 或 API key 提取步骤失败时会静默退出（exit code 2），不产生任何输出。此时用方法二回退。

### 方法二：Python 回退（当脚本静默失败时使用）

```bash
cd ~/knowledge && python3 << 'PYEOF'
import yaml, os, subprocess, json
with open('/home/andymao/.hermes/config.yaml') as f:
    cfg = yaml.safe_load(f)
api_key = cfg.get('providers',{}).get('siliconflow-cn',{}).get('api_key','') \
       or cfg.get('providers',{}).get('siliconflow',{}).get('api_key','')
env = os.environ.copy()
env.update(OPENAI_API_KEY=api_key, OPENAI_BASE_URL='https://api.siliconflow.cn/v1',
           OPENAI_MODEL='Qwen/Qwen3.5-397B-A17B', ENZYME_VAULT_ROOT='/home/andymao/knowledge')
r = subprocess.run(['/home/andymao/.local/bin/enzyme','refresh','--quiet','--use-env-llm'],
                   capture_output=True, text=True, timeout=120, env=env)
d = json.loads(r.stdout) if r.stdout else {}
print(f"Status: {d.get('status')}, New: {d.get('indexing',{}).get('files_new',0)}, Exit: {r.returncode}")
PYEOF
```

## 原理

`enzyme-init.sh` 脚本处理了两层问题：

### 1. LLM 后端选择
Enzyme 的催化剂生成需要调用 LLM，且要求 LLM 支持 `json_object` response_format。

| 后端 | 是否可用 | 原因 |
|------|---------|------|
| Enzyme 托管服务 (app.tryenzyme.com) | ❌ | 代理环境下 TLS 握手超时 |
| DeepSeek V4 (api.deepseek.com) | ❌ | 不支持 `json_object` response_format |
| **SiliconFlow + Qwen3.5-397B-A17B** | ✅ | 支持 JSON mode，催化剂产量高 |

### 2. 脚本自动选择逻辑
```bash
# 1. 从 config.yaml 提取 SiliconFlow API key
# 2. 如果取到 → 用 SiliconFlow + Qwen3.5-397B-A17B
# 3. 如果取不到 → 回退 DeepSeek + deepseek-chat（催化剂可能失败）
```

## 故障排查

### 问题：催化剂生成失败

错误示例：
```
Error: Catalyst generation produced 0 catalysts for 30/30 attempted entities
```

日志检查：
```bash
tail -30 ~/knowledge/.enzyme/enzyme.log | grep -E "WARN|ERROR"
```

典型原因：
- DeepSeek 模型不支持 JSON mode → 改用 SiliconFlow
- API key 无效或过期 → 检查 `~/.hermes/config.yaml` 中 `siliconflow-cn.api_key`
- 模型名称错误 → 检查可用模型列表

### 问题：托管服务不可达

```bash
curl -s --max-time 10 https://app.tryenzyme.com/api/health
```
如果超时，说明托管服务不可用，必须使用 `--use-env-llm` 模式。

## 验证

刷新后检查状态：
```bash
cd ~/knowledge && enzyme status
```

关注指标：
- `Documents` — 文件总数
- `Embedded: X/Y` — 嵌入覆盖率（应为 Y/Y）
- `Catalysts` — 催化剂数量，越多检索越精准

## 已知限制

- Catalyst 生成依赖 LLM 的 JSON mode 能力
- 部分模型（Qwen3-72B, DeepSeek-V3）在 SiliconFlow 上也会失败
- **已验证可用模型**: `Qwen/Qwen3.5-397B-A17B` (催化剂: 73→251)
- 中文笔记的文件名和路径中的中文需要系统支持 UTF-8
- `enzyme refresh` 只增量刷新变更文件，全量重建用 `enzyme init`

## 实用技巧：无 API Key / 无 Credits 时的可用功能

即使 `enzyme refresh` 失败（无 hosted credits 也无 env LLM key），**最基本的向量嵌入仍然正常工作**：

```bash
# enzyme status 使用编译内置的 "ese" 模型 (dim=512)
# 不需要任何 API key 或 credits
cd ~/knowledge && enzyme status
```

输出显示 `Embedded: X/Y` — 这个数值靠编译内嵌的本地模型完成，始终可达 95-100%。

**实际影响：**
- ✅ **向量检索（语义搜索）** — 可用，嵌入模型是编译内置的
- ❌ **催化剂生成（catalyst）** — 不可用，需要 LLM 后端
- ✅ **全文检索** — 永远可用（FTS5 方式，完全本地）

**建议策略：**
- 日常使用 FTS5 全文搜索（`search_files`）为主
- 向量嵌入自动运行，补充语义相似度检索
- 获取 hosted credits 或设置 SiliconFlow API key 后再跑 `enzyme refresh` 生成催化剂
