# Matplotlib 中文图表（Ubuntu 24.04）

## 问题

`matplotlib` 默认不识别 `/usr/share/fonts/opentype/` 下的 `.ttc` 中文字体（如 Noto Sans CJK SC），导致中文显示为方块。

## 完整安装与修复流程

### 1. 安装 matplotlib

```bash
pip3 install matplotlib -q
```

### 2. 确认中文字体存在

```bash
fc-list :lang=zh | grep 'Noto.*Sans.*SC' | head -3
```

期望输出：
```
/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc: Noto Sans CJK SC:style=Regular
```

### 3. Python 中注册字体

```python
import matplotlib
matplotlib.use('Agg')
import matplotlib.font_manager as fm
import os

# 手动添加 opentype 目录下的所有字体（matplotlib 默认不扫描此路径）
for d in ['/usr/share/fonts/opentype/noto/', '/usr/share/fonts/truetype/arphic/']:
    if os.path.isdir(d):
        for fname in os.listdir(d):
            fpath = os.path.join(d, fname)
            if fname.lower().endswith(('.ttf', '.ttc', '.otf')):
                try:
                    fm.fontManager.addfont(fpath)
                except:
                    pass

# 然后 FontProperties 即可使用
fp = fm.FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
```

### 4. 字体缓存问题

如果修改字体配置后无效，清除缓存：

```bash
rm -rf ~/.cache/matplotlib/*
```

### 5. 注意事项

| 事项 | 说明 |
|------|------|
| `.ttc` 格式 | matplotlib 支持 `.ttc`（TrueType Collection），但需要 `addfont()` 手动注册 |
| `use('Agg')` | 无头服务器必须设置 `matplotlib.use('Agg')` 避免 GUI 错误 |
| 备选字体 | 如果 Noto 不可用，尝试 arphic/uming.ttc: `/usr/share/fonts/truetype/arphic/uming.ttc` |
| Emoji 字符 | matplotlib 中文字体不含 Emoji（⭐🔴🟡🟢✅），会显示为缺失，建议去掉 |
| 暗色主题背景 | 使用 `fig.patch.set_facecolor('#1a1a2e')` 和 `ax.set_facecolor('#1a1a2e')` 配合白色文字 |
