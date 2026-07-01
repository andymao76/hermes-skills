---
name: hermes-performance-optimization
description: Hermes Agent 性能优化技能 — 解决响应慢、上下文压缩频繁、工具加载过多等问题
trigger: 用户提到性能慢、卡顿、优化、响应慢、工具加载慢等关键词时自动加载
---

# Hermes Agent 性能优化技能

来源: `~/andymao_Doc/Hermes Agent 性能优化技能.docx`（Andy 环境专用）
适用: Ubuntu 24.04 + Hermes 0.16+

## 一、快速诊断

```bash
hermes doctor               # 全面检查
hermes --version            # 查看版本
hermes update               # 检查更新
hermes doctor --fix         # 自动修复
```

## 二、模型优化

| 场景 | 推荐模型 |
|------|----------|
| 日常问答/CLI交互 | `deepseek-v4-flash` / `qwen/qwen3.6-flash` / `qwen/qwen3.7-plus` |
| 深度分析/复杂项目 | `deepseek-v4-pro` / `claude-opus` / `gpt-5.5` |

```bash
hermes chat -m deepseek-v4-flash
```

## 三、上下文压缩优化

**信号**: 出现 "Preflight compression" / "Compacting context" / "Session compressed"

**方案**:
- 每个项目单独开会话，不要一个会话用几天
- 定期 `hermes session list` + `hermes session delete <id>` 清理历史
- 会话超过 5+ 次交互建议 `/new`

### 压缩模型配置

Hermes 有两个独立的压缩模型配置点，必须全部对齐：

| 位置 | 说明 | 推荐值 (Andy 环境) |
|------|------|-------------------|
| `compression.model` | 会话上下文压缩（session 超长时触发） | `deepseek-v4-flash`, provider `deepseek` |
| `auxiliary.compression` | 辅助压缩（文档/工具结果压缩） | `deepseek-v4-flash`, base_url `https://api.deepseek.com/v1` |

**Andy 环境配置参考（2026-07-01 最终调优）：**
```yaml
# ~/.hermes/config.yaml

# 会话压缩（约第 184 行）
compression:
  enabled: true
  threshold: 0.25                    # 上下文超 ~25% 触发 → 运行时 ~32K (2026-07-01 从 0.375 下调)
  target_ratio: 0.15                 # 压缩到阈值 token 数的 15%
  protect_last_n: 15                 # 保留最近 15 条消息
  protect_first_n: 3                 # 保留最前 3 条（任务目标/开场）
  hygiene_hard_message_limit: 400    # 软上限之外的硬上限
  abort_on_summary_failure: false
  codex_gpt55_autoraise: true
  in_place: true                     # 原地压缩内容而非删除消息
  provider: deepseek
  model: deepseek-v4-flash

# 辅助压缩（约第 216 行）
auxiliary:
  compression:
    provider: deepseek
    model: deepseek-v4-flash
    base_url: https://api.deepseek.com/v1
    api_key: ''           # 通过环境变量 DEEPSEEK_API_KEY 传入
    timeout: 120
    context_length: 131072           # 2026-07-01 从 65536 上调
```

**注意事项：**
- 两处必须用同一模型，否则压缩行为不一致
- api_key 留空，通过 `DEEPSEEK_API_KEY` 环境变量传入（配置文件不留明文密钥）
- 压缩模型不要用本地 Ollama（推理慢、API 兼容性差）
- **阈值 Floor 陷阱：** 单改 `threshold` 和 `context_length` 不够，`MINIMUM_CONTEXT_LENGTH` (model_metadata.py:185) 是硬地板。详见下方「阈值计算链」
- 2026-07-01 全面调优记录详见 `references/compression-parameters-overhaul-20260701.md`

### 压缩压力测试与诊断

需要理解当前压缩行为的实际表现时，使用以下压力测试流程主动触发和分析。

#### 核心原理

压缩触发条件 = `model_real_context × threshold`。例如 DeepSeek V4 Flash 实际 context 约 128K tokens × 0.5 ≈ 64K tokens 时触发（非 config 中 context_length: 65536 的 50%——实际窗口更大）。

#### 诊断脚本

```bash
# 1. 压缩统计概览
echo "=== 今日压缩统计 ==="
grep -c 'compression started' /home/andymao/.hermes/logs/agent.log
grep -c 'compression done' /home/andymao/.hermes/logs/agent.log
echo "=== 触发 Session 数 ==="
grep 'compression started' /home/andymao/.hermes/logs/agent.log | grep -oP 'session=\K\S+' | sort -u | wc -l

# 2. Token 触发点统计
grep -oP 'tokens=~\K[0-9,]+' /home/andymao/.hermes/logs/agent.log | tr -d ',' | \
  awk 'BEGIN{min=999999;max=0} {if($1>0){if($1<min)min=$1;if($1>max)max=$1;sum+=$1;cnt++}} \
  END{printf "avg=%.0f min=%d max=%d count=%d\n", sum/cnt, min, max, cnt}'

# 3. 压缩耗时统计
python3 -c "
import re
with open('/home/andymao/.hermes/logs/agent.log') as f:
    lines = f.readlines()
pairs = {}
for i, line in enumerate(lines):
    if 'compression started' in line:
        m = re.search(r'(\d{2}:\d{2}:\d{2}),\d+', line)
        if m: pairs[i] = ('start', m.group(1))
    if 'compression done' in line:
        m = re.search(r'(\d{2}:\d{2}:\d{2}),\d+', line)
        if m: pairs[i] = ('done', m.group(1))
starts = [k for k,v in pairs.items() if v[0]=='start']
dones = [k for k,v in pairs.items() if v[0]=='done']
times = []
for s,d in zip(starts,dones):
    sh,sm,ss = pairs[s][1].split(':'); dh,dm,ds = pairs[d][1].split(':')
    sec = (int(dh)*3600+int(dm)*60+int(ds)) - (int(sh)*3600+int(sm)*60+int(ss))
    if 0 < sec < 120: times.append(sec)
if times: print(f'平均耗时: {sum(times)/len(times):.1f}s\t最短: {min(times)}s\t最长: {max(times)}s\t样本数: {len(times)}')
"

# 4. 最近 20 条压缩日志
grep 'conversation_compression' /home/andymao/.hermes/logs/agent.log | tail -20

# 5. 压缩风暴检测（连续高频触发）
grep 'compression started' /home/andymao/.hermes/logs/agent.log | \
  awk '{print $1,$2,$10}' | sort -u
```

#### 重要: 使用 Python 而非 awk 进行日志分析

awk 的正则回溯引用 (`\1` 在匹配模式中) 在大多数 awk 实现中不工作。如果你需要匹配 `messages=11→11` 这类前后相同时的模式，**必须使用 Python**:

```bash
python3 -c "
import re
with open('/home/andymao/.hermes/logs/agent.log') as f:
    for line in f:
        m = re.search(r'session=(\S+).*?messages=(\d+)->(\d+)', line)
        if m and m.group(2) == m.group(3):
            print(f'FAIL: {m.group(1)} → {m.group(2)}→{m.group(3)}')
"
```

awk 适用于简单的行号/字段统计，但涉及模式匹配中的捕获组回溯引用时务必换用 Python。

#### 理解输出

| 字段 | 含义 |
|------|------|
| `messages=19` | 压缩触发时的消息数 |
| `tokens=~67,190` | 估算 token 数（rough_tokens，非精确值） |
| `messages=11->9` | 压缩前后消息数变化：11→9 = 已合并消息；11→11 = in_place 内容压缩 |
| `awaiting_real_usage=true` | 压缩后的 token 数为估算，待 API 返回实际值 |
| `context compression started|done` | 一次完整压缩周期 |

**三种压缩模式对比：**
- `N→N` 等量（如 29→29, 11→11）：in_place 模式，压缩消息内容但不删除消息框架
- `N→M` 减少（如 11→9, 12→8）：合并模式，相邻消息被摘要合并
- `N→N` 但 token↑：极端情况——压缩后的 rough token 估算反而升高（awaiting_real_usage=true 的副作用）

#### 主动触发压缩的测试方法

当需要验证压缩是否正常工作（如更换压缩模型后）：

1. 读取 config 中的压缩配置确认参数
2. 读取 agent.log 尾部获取当前 session 的压缩基准线
3. 通过多轮分析逐步构建上下文（重复读取、grep、分析操作）
4. 监控上下文膨胀——每轮注入 5K-15K tokens 的分析内容
5. 当上下文超过 threshold 时，Hermes 会自动执行压缩，输出 `[CONTEXT COMPACTION — REFERENCE ONLY]` 通知

预期：DeepSeek V4 Flash 压缩 ~67K tokens 约 **17 秒**（范围 7-35s），远低于默认 120s timeout。

详细压力测试记录和指标见 `references/compression-stress-test.md`。

### 阈值计算链（调优必读）

压缩触发阈值不是直接由 `threshold` 或 `context_length` 任一个决定的，而是经过一个完整计算链：

```
effective_window = context_length - max_tokens    # max_tokens 通常=None，故≈context_length
pct_value = int(effective_window × threshold_percent)
floored = max(pct_value, MINIMUM_CONTEXT_LENGTH)   # ← 关键 Floor！
threshold_tokens = floored                         # （除非退化守卫触发）
tail_token_budget = int(threshold_tokens × target_ratio)
```

**致命陷阱：MINIMUM_CONTEXT_LENGTH Floor**

即使你把 `threshold` 降到 0.1，如果 `MINIMUM_CONTEXT_LENGTH` 是 64K，触发阈值依然最低 64K。这就是 2026-07-01 之前日志一直显示 `threshold: 48K` 但实际触发在 64K 的根因——百分比计算值被 Floor 抬升了。

**如何验证：**
```bash
python3 -c "
from agent.model_metadata import MINIMUM_CONTEXT_LENGTH
from agent.context_compressor import ContextCompressor
threshold = ContextCompressor._compute_threshold_tokens(131072, 0.25, None)
print(f'threshold_tokens = {threshold}')
print(f'tail_token_budget = {int(threshold * 0.15)}')
"
```

### 空循环强制压缩机制（2026-07-01 新增）

**问题：** 当上下文大部分是摘要/历史时，`compress()` 找不到新的可压缩窗口（`compress_start >= compress_end`），压缩徒耗辅助 API 调用。现有反抖动逻辑在 2 次无效压缩后完全跳过压缩，导致上下文无限增长。

**解决方案 — 三击断路器 + 激进模式：**

在 `context_compressor.py` 中实现：

| 无效压缩计数 | 行为 |
|---|---|
| 1 次 | 正常继续，递增计数器 |
| 2 次 | 跳过压缩（现有行为） |
| ≥3 次 | **强制激进压缩** — 收紧尾保护参数，打破死锁 |

激进模式参数：
- `protect_last_n` 降至 `max(8, current - 7)`
- `tail_token_budget` 砍半（原 4915 → ~2457）
- 单次压缩后自动重置标志，恢复正常参数

**修改点（context_compressor.py）：**
1. `__init__` — 添加 `self._aggressive_compress_requested: bool = False`
2. `should_compress()` — `_ineffective_compression_count >= 3` 时设置激进标志并返回 True 而非跳过
3. `compress()` 中 Phase 1 — 检测激进标志，使用收紧的尾保护参数
4. `compress()` 末尾 — 压缩完成后重置激进标志

**日志信号：**
- `Compression in aggressive mode — last N compressions saved <10% each. Tightening tail parameters.`
- `Aggressive compression: protect_last_n=X, tail_budget=Y`

### 压缩失败率深度分析

**核心公式：**
```
失败率 = 空循环压缩 / 总压缩数
空循环 = messages_N → messages_N（in_place 模式下内容压缩但消息数不变）
```

**历史基线（2026-07-01 第一次修复前）：**
- 全天 42% 压缩为空循环 (33/79)
- 最坏 session: `094905_8980ba` — 8 次压缩中 6 次无效 (75%)
- 根因：threshold 0.5 导致触发点在 ~64K，压缩后仍高于新阈值 → 立即重触发

**2026-07-01 修复历程：**

| 轮次 | 操作 | 效果 |
|------|------|------|
| 1 | threshold 0.5 → 0.375 | 触发点从 ~64K 降至 ~48K，打破立即重触发循环 |
| 2 | MINIMUM_CONTEXT_LENGTH 64K → 32K | 去除 Floor 对阈值下限的抬升 |
| 3 | threshold 0.375 → 0.25 | 触发点降至 ~32K |
| 4 | context_length 65K → 131K | 扩大窗口，减少总压缩频次 |
| 5 | target_ratio 0.2 → 0.15 | 每个压缩周期释放更多 token |
| 6 | protect_last_n 20 → 15 | 减少尾保护消息数，增加可压缩窗口 |
| 7 | 空循环强制压缩机制 | 防止 ≥3 次无效压缩后完全跳过压缩的死锁 |

**验证新参数链：**
```
model.context_length = 131072
compression.threshold = 0.25
effective_window = 131072
pct_value = int(131072 × 0.25) = 32768
floored = max(32768, 32768) = 32768        ← 不再被 MINIMUM_CONTEXT_LENGTH 抬升
threshold_tokens = 32768
tail_token_budget = 32768 × 0.15 ≈ 4915
```

### 系统化行为分析 5 轮方法论

当需要系统性诊断 Hermes 的某种行为(性能、压缩、循环)时, 采用以下结构化方法:

| 轮次 | 目标 | 典型操作 |
|------|------|----------|
| 1 | 配置基线确认 | 读取 config.yaml 相关段 |
| 2 | 单 session 观察 | 测本轮工具调用后的 token/消息变化 |
| 3 | 全局统计 | 提取所有 session 的分布、频次 |
| 4 | 失败/异常分析 | 识别最坏 case, 计算失败率 |
| 5 | 根因诊断+建议 | 关联配置与行为, 给出修复方案 |

每轮结果输出到临时文件, 最后合成为最终报告。

## 四、工具集精简

| 场景 | 命令 |
|------|------|
| 运维 | `hermes chat -t terminal,file` |
| 运维+搜索 | `hermes chat -t terminal,file,web` |
| 开发 | `hermes chat -t terminal,file,web,code_execution` |
| 普通问答 | `hermes chat -t web` |

## 五、代理配置

```bash
export HTTP_PROXY=http://127.0.0.1:7897
export HTTPS_PROXY=http://127.0.0.1:7897
export NO_PROXY=localhost,127.0.0.1,::1
```

永久生效写入 `~/.bashrc`

## 六、Gateway 优化

```bash
hermes gateway install      # 安装为系统服务
hermes gateway start        # 后台常驻
hermes gateway status       # 查看状态
```

避免每次启动重复加载 Gateway。

## 七、系统依赖

```bash
# 基础
sudo apt install -y git ripgrep fd-find jq curl unzip build-essential python3-pip python3-venv nodejs npm
# Browser 工具
sudo apt install -y xvfb xdotool x11-utils scrot imagemagick fonts-noto-cjk
```

## 八、性能监控

```bash
htop      # CPU
free -h   # 内存
df -h     # 磁盘
uptime    # 负载
```

## 九、启动模板

| 模式 | 命令 |
|------|------|
| 运维 | `hermes chat -t terminal,file -m deepseek-v4-flash` |
| 搜索 | `hermes chat -t terminal,file,web -m deepseek-v4-flash` |
| 研发 | `hermes chat -t terminal,file,web,code_execution -m deepseek-v4-pro` |
| 知识库 | `hermes chat -t terminal,file,web,memory -m qwen/qwen3.7-plus` |

## 十、更新后工作流

更新 Hermes 后，建议执行以下步骤记录版本变更：

```bash
# 1. 记录版本信息到本地知识库
# 写入 ~/knowledge/Hermes/Hermes-Agent-版本记录.md
# 格式示例（日期+version+upstream commit+变更明细表格）

# 2. 刷新语义索引，使新内容可搜索
cd ~/knowledge && kb-index index
```

关键信息: 更新前 commit、更新后 commit、新增 commit 数、变更明细（git log）、更新过程
注意（依赖/Web UI/skill 保留）。参考 `~/knowledge/Hermes/Hermes-Agent-版本记录.md`。

## 十一、最佳实践

优先级:
1. 使用 Flash 模型
2. 控制会话长度（5+ 交互 /new）
3. 精简工具集
4. 修复代理配置
5. 定期更新 Hermes（更新后记录版本历史到 KB）
6. 启用 Gateway 服务
7. 安装 Browser 依赖
8. 监控资源占用

## Andy 环境默认配置

```yaml
系统: Ubuntu 24.04.4 LTS
Python: 3.12
Hermes: 0.16.x
代理: 127.0.0.1:7897
默认启动: hermes chat -t terminal,file,web -m deepseek-v4-flash
适用: Linux运维, 大数据平台巡检, Kafka/Flink, OpenWebUI, Dify, Neo4j, Obsidian, Hermes开发
```
