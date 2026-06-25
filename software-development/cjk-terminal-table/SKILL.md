---
name: cjk-terminal-table
description: Python 终端表格 CJK 对齐方案 — 用 _dw() + _pad() 替代 str.ljust/center/rjust 和 format(:<), 解决中文占 2 列但 Python 算 1 列的错位问题。
trigger: 需要在 Python 终端输出含中文的表格时；用户说表格不对齐、错位、不美观时
---

# CJK 终端表格对齐

## 问题

Python 的 `str.ljust()`、`str.center()`、`str.rjust()` 和 `f"{s:<10}"` 格式符，都按 **Python 字符数**（`len(s)`）计算宽度。但中文字符（CJK）在终端中占 **2 列**，导致含中文的表格列实际宽度超出边框，出现偏移。

## 核心工具函数

```python
def _dw(s):
    """计算字符串在终端中的显示宽度（CJK 占 2 列，ASCII 占 1 列）"""
    w = 0
    for c in s:
        if '\u4e00' <= c <= '\u9fff' or '\u3000' <= c <= '\u303f' or '\uff00' <= c <= '\uffef':
            w += 2
        else:
            w += 1
    return w


def _pad(s, w, align='l'):
    """按终端显示宽度填充/对齐字符串
    align: 'l' 左对齐, 'r' 右对齐, 'c' 居中
    """
    sw = _dw(s)
    gap = w - sw
    if gap <= 0:
        return s
    if align == 'r':
        return ' ' * gap + s
    elif align == 'c':
        left = gap // 2
        right = gap - left
        return ' ' * left + s + ' ' * right
    else:
        return s + ' ' * gap
```

## 完整表格模板

```python
def show_table():
    # 列宽（终端列数，CJK 按 2 算）
    COL_A = 10   # 例："餐前(空腹)" 占 10 列
    COL_B = 12   # 例："糖尿病(诊断)" 占 12 列
    COL_C = 8
    COL_D = 8
    GAP = 3        # " │ "
    PAD_L = 2      # 左侧缩进 "  "
    INNER = PAD_L + COL_A + GAP + COL_B + GAP + COL_C + GAP + COL_D + 1
    CORNERS = {'┌': '┐', '├': '┤', '└': '┘'}

    def sep(ch='├'):
        return f"  {ch}{'─' * INNER}{CORNERS.get(ch, '┤')}"

    def title_line(title):
        left = (INNER - _dw(title)) // 2
        right = INNER - _dw(title) - left
        return f"  │{' ' * left}{title}{' ' * right}│"

    print()
    print(sep('┌'))
    print(title_line("表格标题"))
    print(sep())
    print(f"  │  {_pad('列A', COL_A)} │ {_pad('列B', COL_B)} │ {_pad('数值C', COL_C, 'r')} │ {_pad('数值D', COL_D, 'r')} │")
    print(sep())

    for row in rows:  # rows 为 [(a, b, c, d), ...]
        cond, label, val_c, val_d = row
        print(f"  │  {_pad(cond, COL_A)} │ {_pad(label, COL_B)} │ {_pad(val_c, COL_C, 'r')} │ {_pad(val_d, COL_D, 'r')} │")
        # 分隔行用 print(sep())

    print(sep('└'))
    print()
```

## 关键点

1. **列宽设计**：先确定数据中最宽的字符串的终端宽度（CJK 数 ×2 + ASCII 数），设为此列宽
2. **标题居中**：用 `_dw(title)` 计算标题真实宽度，再算左右空白，**不要用** `str.center()`
3. **数值右对齐**：`align='r'`
4. **角字符映射**：用 `CORNERS` 字典确保 `┌` 配 `┐`、`├` 配 `┤`、`└` 配 `┘`
5. **内间距**：`INNER` 包含 PAD_L（左侧缩进）+ 各列宽 + 间隔 + 右侧 1 空格

## 常见错误

- ❌ 直接用 `f"{'条件':<10}"` — 中文 "条件" 终端占 4 列，实际显示宽度 10+2=12
- ❌ 标题用 `"标题".center(48)` — 同个问题，终端占位大于 48
- ❌ 边框 `'─'` 数量硬编码 — 应与 `INNER` 绑定，动态计算
- ✅ 边框宽度 `INNER` 用公式自动计算，所有行保持一致

## 典型应用

- 诊断标准对照表
- 配置参数展示
- 数据统计报表
- 中英文混合表格
