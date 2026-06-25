# Ubuntu 24.04 输入法配置 (IBus + GNOME)

IBus 是 Ubuntu GNOME 桌面默认输入法框架。以下配置在新安装系统或重置后使用。

## 场景

- 用户说"默认输入法改英文"、"切换中文输入"、"改系统语言"
- 用户说"输入法快捷键"、"Ctrl+Shift切换输入法"
- 用户说"locale 问题"、"LANG=zh_CN"

## 关键概念

| 术语 | 含义 |
|------|------|
| `sources` | 已启用的输入源列表。顺序 = 优先级。第一个是默认。 |
| `mru-sources` | 最近使用的输入源。GNOME 会记住上次用的输入法，下次自动切回去。 |
| `switch-input-source` | 键盘快捷键，切换输入源。 |
| locale (LANG) | 系统语言。`zh_CN.UTF-8` 会导致 IBus 自动启用中文输入模式。 |

## 常用命令

### 查看当前配置

```bash
# 输入源列表（排序决定默认）
gsettings get org.gnome.desktop.input-sources sources
# 期望: [('xkb', 'us'), ('ibus', 'libpinyin')]

# 最近使用的输入源
gsettings get org.gnome.desktop.input-sources mru-sources
# 期望: [('xkb', 'us')]

# 切换快捷键
gsettings get org.gnome.desktop.wm.keybindings switch-input-source
# 期望: ['<Control>Shift_L']  (Ctrl+Shift)

# locale
cat /etc/default/locale
```

### 设置默认输入法为英文（保留中文切换能力）

```bash
# 1. 设置输入源顺序：英文优先
gsettings set org.gnome.desktop.input-sources sources "[('xkb', 'us'), ('ibus', 'libpinyin')]"

# 2. 清空 MRU（不要记住上次用的中文）
gsettings set org.gnome.desktop.input-sources mru-sources "[('xkb', 'us')]"

# 3. 重启 IBus 立即生效
ibus restart
```

### 设置切换快捷键为 Ctrl+Shift

```bash
# 向前切换（英文↔中文）
gsettings set org.gnome.desktop.wm.keybindings switch-input-source "['<Control>Shift_L']"

# 向后切换
gsettings set org.gnome.desktop.wm.keybindings switch-input-source-backward "['<Shift><Control>Shift_L']"
```

### 仅保留英文输入源

```bash
gsettings set org.gnome.desktop.input-sources sources "[('xkb', 'us')]"
```

### 修改系统语言（UI 英文 + 默认英文输入）

```bash
sudo update-locale LANG=en_US.UTF-8
# 或手动编辑 /etc/default/locale
# 注销重新登录生效
```

## 踩坑

1. **`zh_CN.UTF-8` locale 自动启用中文输入** — 即便 sources 里英文在第一，locale 为中文时部分 GTK 应用仍默认切到拼音。改 locale 到 `en_US.UTF-8` 可根治，但系统 UI 会变英文。
2. **MRU 会覆盖 sources 顺序** — 如果用户最后用了中文输入，下次打开应用默认还是中文。必须显式 reset MRU。
3. **`switch-input-source` 的 gsettings 键路径** — 在 `org.gnome.desktop.wm.keybindings` 下，不是 `org.gnome.desktop.input-sources`。
4. **Ctrl+Shift 可能与应用冲突** — 终端里 Ctrl+Shift+V 粘贴、Ctrl+Shift+T 开新标签、IDE 中 Ctrl+Shift 快捷键。如果冲突太多，可改为 `['<Control>space']`（Ctrl+空格）作为备选。
5. **修改后需注销或重启会话才完全生效** — `ibus restart` 立即生效于当前桌面，但某些 GNOME 行为（如按键绑定）需重新登录。
