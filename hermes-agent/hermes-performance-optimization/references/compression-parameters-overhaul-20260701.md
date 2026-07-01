# 压缩参数全面调优记录 (2026-07-01)

## 背景

Hermes Agent 持续压缩失败率高达 42%: 79 次压缩中 33 次为空循环。最坏情况 session `094905_8980ba` 在 5 分钟内执行 8 次压缩，6 次完全无效。

## 根因分析

两层原因叠加导致压缩失效：

### 原因 1: threshold 过高导致死循环

```
model.context_length = 65536
compression.threshold = 0.5
触发点 ≈ 65536 × 0.5 ≈ 32K
但 MINIMUM_CONTEXT_LENGTH = 64000 把阈值抬到 64K
→ 压缩后 token 仍 ~63K 高于 ~64K → 立即再压缩
```

### 原因 2: MINIMUM_CONTEXT_LENGTH Floor 掩蔽

`agent/model_metadata.py:185`:
```python
MINIMUM_CONTEXT_LENGTH = 64_000  # 硬件最低门槛
```

即使 `threshold_percent` 计算出 24K，`max(24K, 64K) = 64K`，64K 成为实际触发阈值。

### 完整计算链

```
effective_window = context_length - max_tokens  # max_tokens=None
pct_value = int(effective_window × threshold_percent)
floored = max(pct_value, MINIMUM_CONTEXT_LENGTH)   # 关键 Floor
threshold_tokens = floored
tail_budget = int(threshold_tokens × target_ratio)
```

## 修改清单

### model_metadata.py:185
- `MINIMUM_CONTEXT_LENGTH = 64_000` → `32_768`

### config.yaml (via `hermes config set`)
| 参数 | 旧值 | 新值 |
|---|---|---|
| `model.context_length` | 65536 | 131072 |
| `compression.threshold` | 0.375 | 0.25 |
| `compression.target_ratio` | 0.2 | 0.15 |
| `compression.protect_last_n` | 20 | 15 |
| `auxiliary.compression.context_length` | 65536 | 131072 |

### context_compressor.py — 空循环强制压缩

**新增字段:**
```python
self._aggressive_compress_requested: bool = False
```

**修改 should_compress() — 反抖动逻辑:**
- `_ineffective_compression_count >= 2`: 跳过压缩（现有行为）
- `_ineffective_compression_count >= 3`: 设置激进标志，允许压缩

**修改 compress() — Phase 1 预剪枝:**
```python
if self._aggressive_compress_requested:
    _aggressive_protect_n = max(8, self.protect_last_n - 7)
    _aggressive_tail_budget = int(self.tail_token_budget * 0.5)
```

**compress() 末尾:** 重置 `_aggressive_compress_requested = False`

## 验证结果

### 阈值验证
```
effective_window = 131072
pct_value = int(131072 * 0.25) = 32,768
floored = max(32,768, 32,768) = 32,768    ← Floor 不再支配
threshold_tokens = 32,768
tail_token_budget = 32,768 × 0.15 ≈ 4,915
```

### 语法验证
- `MINIMUM_CONTEXT_LENGTH = 32768` ✅
- `should_compress()` 含 `_aggressive_compress_requested` 和 `>= 3` 检查 ✅
- `__init__` 含 `_aggressive_compress_requested: bool = False` ✅
- `compress()` 含激进模式分支 ✅
- config 参数全部正确写入 ✅

## 重启后需观察

1. 日志中触发阈值从 ~64K 变为 ~32K
2. 压缩失败率从 42% 下降
3. 激进模式日志是否被触发（信号: `Aggressive compression: protect_last_n=`）
4. 留意辅助 API 调用量是否因激进模式增加
