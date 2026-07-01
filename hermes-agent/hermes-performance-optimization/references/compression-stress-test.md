# 压缩压力测试记录 — 全量历史

> **最新参数 (2026-07-01 最终调优)** 详见 `references/compression-parameters-overhaul-20260701.md`

## 配置演进

| 日期 | threshold | context_length | MINIMUM_CONTEXT_LENGTH | target_ratio | protect_last_n |
|---|---|---|---|---|---|
| 修复前 | 0.5 | 65536 | 64000 | 0.2 | 20 |
| 第一次修复 | 0.375 | 65536 | 64000 | 0.2 | 20 |
| **最终调优** | **0.25** | **131072** | **32768** | **0.15** | **15** |

---

## 修复前基线 (threshold=0.5)

### 关键指标

**全天 79 次压缩，33 次失败 (42%)**

| 指标 | v1(早段) | v2(全天) |
|------|----------|----------|
| 压缩总次数 | 63 start / 63 done | 79 start / 79 done |
| 涉及的 Session 数 | 62 | 61 |
| 总失败(消息数无变化) | — | **33 / 79 = 42%** |
| 最坏 session 失败数 | — | **6/8 (75%)** |
| 平均压缩后 token | — | **67,965** (> threshold!) |
| 触发70K+的 session | — | 14 次 |

### 最坏 case: session 094905_8980ba

10:03→10:08 五分钟内 8 次压缩，6 次无效：

```
✓ 11→9  (有效, token↓)
✓ 12→8  (有效, token↓)
✗ 11→11 (无效 — 死循环开始)
✗ 14→14 (无效 — token还在涨)
✗ 17→17 (无效)
✗ 19→19 (无效)
✗ 22→22 (无效)
✗ 25→25 (无效)
```

### 根因: 死区陷阱

```
threshold × window = 0.5 × ~128K = 64K   (触发线)
压缩后 token ≈ 67K                        (典型值)
差值: 67K - 64K = 3K → 仍在触发线之上!
f(x)=max(0.5x, 64K) → 最小值永远是64K   ← Floor 陷阱
```

### 压缩耗时分布

DeepSeek V4 Flash 在修复前基线的压缩延迟：

| 消息数 | token 数 | 耗时 |
|--------|----------|------|
| 19 | ~67K | ~21s |
| 24 | ~68K | ~17s |
| 29 | ~69K | ~13s |
| 31 | ~69K | ~11s |
| 34 | ~70K | ~20s |
| 36 | ~70K | ~10s |
| 38 | ~70K | ~19s |
| 40 | ~70K | ~15s |
| 42 | ~70K | ~9s (缓存预热后) |

趋势：连续压缩因 API 缓存预热，耗时从 21s 降至 9s。

### 压缩模式分布

| 模式 | 比例 | 说明 |
|------|------|------|
| `N→N` 等量 | ~60% | in_place 内容摘要，消息框架不变 |
| `N→M` 减少 | ~30% | 合并相邻消息 |
| `N→N` token↑ | ~10% | rough token 估算异常 |

### 风暴模式时间线

```
08:24-08:50  ■■■■■■■■■■■■■■■■■■■■  26次 (间隔~40s)
08:50-09:00  ■■■■■■■■■■■■■■■■■■■  21次 (持续)
09:04-09:06  ■■■■■■■■■  9次 (密集, 间隔5-20s)
10:03-10:05  ■■■■  4次
```

## 第一次修复后基线 (threshold=0.375)

threshold 从 0.5 → 0.375 后，触发点从 ~64K 降至 ~48K：

```
threshold × ~128K ≈ 48K  → 提前触发避免堆积
压缩后 token ≈ 45K-50K   → 低于阈值，循环打破
```

失败率从 42% 显著下降，但仍有残留空循环，因为 MINIMUM_CONTEXT_LENGTH=64K 硬地板未动。

## 最终修复 (2026-07-01 综合调优)

见 `references/compression-parameters-overhaul-20260701.md` 完整记录。

### 验证监控脚本

```bash
# 检查连续失败 (≥3次 = 需关注)
python3 -c "
import re
with open('/home/andymao/.hermes/logs/agent.log') as f:
    lines = f.readlines()
fail_streaks = {}
for line in lines:
    if 'compression done' not in line:
        continue
    m = re.search(r'session=(\S+).*?messages=(\d+)->(\d+)', line)
    if not m: continue
    sid, b, a = m.group(1), int(m.group(2)), int(m.group(3))
    if sid not in fail_streaks:
        fail_streaks[sid] = {'consecutive': 0, 'max_streak': 0}
    if b == a:
        fail_streaks[sid]['consecutive'] += 1
        fail_streaks[sid]['max_streak'] = max(fail_streaks[sid]['max_streak'], fail_streaks[sid]['consecutive'])
    else:
        fail_streaks[sid]['consecutive'] = 0
bad = {k: v for k, v in fail_streaks.items() if v['max_streak'] >= 3}
if bad:
    for sid, d in sorted(bad.items(), key=lambda x: -x[1]['max_streak']):
        print(f'⚠ {sid}: max_streak={d[\"max_streak\"]}')
else:
    print('✓ 无连续3次以上失败')
"

# 检查激进模式是否被触发
grep -c 'Aggressive compression' /home/andymao/.hermes/logs/agent.log
```
