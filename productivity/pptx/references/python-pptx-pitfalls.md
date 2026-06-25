# python-pptx 常见陷阱

## Inches() 返回值是 EMU，不是浮点数

**错误用法:**
```python
Inches(0.8) + 0.2   # → 914400 EMU + 0.2 EMU ≈ 914400 (偏移几乎为0)
```

为什么：`Inches()` 返回 `int`（EMU 值），`Inches(0.8) = 914400`。加 `0.2` 是在 EMU 尺度上加 0.2 EMU，不是 0.2 英寸。

**正确用法:**
```python
Inches(0.8) + Inches(0.2)  # → 914400 + 228600 = 1143000 (正确偏移0.2英寸)
```

**症状：** 所有内部偏移量（卡片左边框、文字距卡片边缘的距离）几乎为零，文字全部堆到最左边。

**修复检查清单:**
- [ ] 所有 `l + 0.2` → `l + Inches(0.2)`
- [ ] 所有 `t + 0.3` → `t + Inches(0.3)`
- [ ] 所有 `w - 0.5` → `w - Inches(0.5)`

## 函数参数名避免冲突

在 `def` 中同时使用 `t` 作为「top 位置」和「text 内容」会导致重名冲突：
```python
# ❌ 错误
def TX(s, l, t, w, h, t):  # t 同时是 top 和 text
    ...
    p.text = t  # 引用的是 top 参数

# ✅ 正确
def TX(s, l, t, w, h, txt):  # txt 作内容，t 作位置
    ...
    p.text = txt
```

## 其他注意事项

- `RGBColor(0x33, 0x4)` 缺少第三个参数 → 应为 `RGBColor(0x33, 0x33, 0x44)`
- 列表传给 `TX()`（期望字符串）→ 应使用 `BL()`
- `slides` 变量名冲突（与 `prs.slides` 属性重名）
