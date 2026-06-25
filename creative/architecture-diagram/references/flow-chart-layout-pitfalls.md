# Flow Chart Layout Pitfalls — 流程图布局避坑

## 核心问题：决策菱形与下游步骤重叠

决策菱形 (`<polygon>`) 的 Y 轴范围比 visible 边界更宽。菱形 center=(cx,cy) 的高度为 h 时，顶点在 `cy ± h/2`，但左右顶点也在 cy 位置形成视觉上的"宽腰"。

### 典型错误案例

**错误布局：** 将"Step 7"放在菱形右侧同一 Y 行

```
                  [需查知识库?]  ← 菱形 span y=395~495
                  /          \
             是 /              \ 否
              ↓                 ↓
        [Step 6 KB]    [Step 7 生成响应]  ← y=420~480 ❌ 与菱形重叠！
```

**问题：** Step 7 的 y=420~480 和菱形的 y=395~495 垂直重叠，视觉上混在一起。

### 正确做法

Step 7 必须放在菱形下方，而非同一行：

```
                  [需查知识库?]  ← 菱形 span y=395~455
                  /          \
             是 /              \ 否
              ↓                 ↓
        [Step 6 KB]     (直接生成)
              \             /
               \           /
              [Step 7 生成响应]  ← y=515~575 ✅ 完全在菱形下方
                    ↓
              [Step 8 返回]
```

### 坐标计算公式

```
diamond_cy     = 期望的菱形中心 Y 坐标
diamond_h      = 菱形高度（顶点到底点的 Y 距离）
diamond_top    = diamond_cy - diamond_h/2
diamond_bottom = diamond_cy + diamond_h/2

# 下游 box 的最小 Y 坐标
box_min_y = diamond_bottom + 最小间距(≥40px)

# 侧分支（lateral branch）的 Y 坐标
# 如果必须放在菱形同一行，该 box 的 top 必须 ≥ diamond_top
# 且 box 的 left 必须在 diamond 的 left 点左侧，有足够间距
```

### 完整验证清单

生成流程图 SVG 后，逐一检查：

| 检查项 | 方法 |
|--------|------|
| 菱形底部 < 下方 box 顶部 | `diamond_bottom + gap ≤ box_top` |
| 菱形右顶点 < 右侧 box 左边缘 | `diamond_right_x + gap ≤ box_left_x`（且 Y 不重叠） |
| 箭头路径不穿过 box | 中间节点 x1/y1 → x2/y2 路径有缓冲 bend |
| 文字不超出 box | text-anchor=middle, x=box_center_x |
| 子步骤 Y 不对齐 | 同一层级的 box 应当 Y 对齐 |

### 快速修复步骤

当发现菱形与 box 重叠时：

1. 计算菱形 bottom = `cy + h/2`
2. 将冲突 box 的 Y 设为 `diamond_bottom + 40`
3. 调整该 box 的所有入/出箭头的 Y 坐标
4. 如果 box 有下游步骤，级联调整
5. 增大 viewBox 高度以容纳扩展后的内容
