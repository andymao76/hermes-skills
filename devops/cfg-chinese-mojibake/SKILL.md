---
name: cfg-chinese-mojibake
description: 排查与修复 .cfg/.conf/.ini 等配置文件中文注释乱码问题 — 当 file/enca 显示 UTF-8、locale 正常、echo 中文正常但 cat/vim 仍乱码时使用
trigger: 用户反馈 .cfg 文件中文注释乱码、配置文件中文显示为 æŽ¥å�£ 等乱码字符、中文配置乱码、mojibake
category: devops
---

# .cfg 中文注释乱码排查与修复

## 适用场景

当 `.cfg`、`.conf`、`.ini` 等配置文件中的中文注释显示为乱码，例如：

```text
x2ã€�x3æŽ¥å�£ä½¿ç”¨ftpæ–¹å¼�
æ¨¡å�—å†…éƒ¨tcpé€šä¿¡ipåœ°å�€
```

但系统 `locale` 正常、`file/enca/iconv` 又显示文件是 UTF-8 时，可使用本 Skill 排查。

---

## 一、典型现象

```
cat A-su-cs-ztlig.cfg
```

中文注释乱码。

检查文件编码：

```bash
enca A-su-cs-ztlig.cfg
```
输出：`Universal transformation format 8 bits; UTF-8`

检查系统语言环境：

```bash
locale
```
输出类似：
```text
LANG=zh_CN.UTF-8
LC_CTYPE="zh_CN.UTF-8"
LC_ALL=zh_CN.UTF-8
```

继续检查：

```bash
file -i A-su-cs-ztlig.cfg
iconv -f UTF-8 -t UTF-8 A-su-cs-ztlig.cfg -o /dev/null
```
输出：`charset=utf-8`，`iconv` 无报错。

同时：

```bash
echo "中文测试"
```
显示正常。

---

## 二、关键判断结论

如果同时满足：

1. `enca` 显示 UTF-8
2. `file -i` 显示 `charset=utf-8`
3. `iconv -f UTF-8 -t UTF-8` 不报错
4. `locale` 是 `zh_CN.UTF-8` 或其他 UTF-8
5. `echo "中文测试"` 显示正常
6. 但 `cat/vim` 打开该 `.cfg` 仍显示乱码

则基本可以判断：

> 文件当前是"合法 UTF-8"，但其中的中文内容已经被错误转码后保存了。
> 这不是终端问题，也不是 Linux locale 问题，而是内容层面的二次乱码。

---

## 三、根因

本次问题的真实原因是：

> `.cfg` 文件曾通过非中文 Windows 环境下的 MobaXterm 打开后，使用复制/粘贴方式重新生成或保存，导致中文注释在剪贴板/终端显示过程中发生错误转码。

也就是：

```text
原始 UTF-8 中文
    ↓
MobaXterm / Windows 非中文环境错误解释为 ANSI / Latin1 / CP1252
    ↓
复制到剪贴板
    ↓
再次保存为 UTF-8
    ↓
形成合法 UTF-8 的乱码字符
```

典型乱码示例：

```text
æŽ¥å�£  → 原本是 "接口"

E6 8E A5 E5 8F A3  → 正确的 UTF-8 字节
```

错误保存后，乱码字符本身已成为合法 UTF-8 字符串，所以 `file -i`、`enca`、`iconv` 都会认为文件是 UTF-8。

---

## 四、排查流程

### 1. 检查文件编码

```bash
enca A-su-cs-ztlig.cfg
file -i A-su-cs-ztlig.cfg
```

期望：
```text
UTF-8
charset=utf-8
```

### 2. 验证 UTF-8 合法性

```bash
iconv -f UTF-8 -t UTF-8 A-su-cs-ztlig.cfg -o /dev/null
```

无输出、无报错，表示文件是合法 UTF-8。

### 3. 检查系统 locale

```bash
locale
```

期望包含：
```text
LANG=zh_CN.UTF-8
LC_CTYPE="zh_CN.UTF-8"
LC_ALL=zh_CN.UTF-8
```

### 4. 检查终端中文显示能力

```bash
echo "中文测试"
```

如果正常，说明终端、locale、SSH 客户端基本没有问题。

### 5. 查看前几行内容

```bash
nl -ba A-su-cs-ztlig.cfg | head -30
```

如果出现：
```text
ã€�
æŽ¥å�£
ä½¿ç”¨
æ¨¡å�—
```

说明很可能是 UTF-8 被错误按 ANSI/Latin1 解释后又保存。

---

## 五、修复方案

### 方案 A：最可靠 — 重新获取原始文件

推荐使用：
```bash
scp
sftp
rsync
rz/sz
MobaXterm SFTP Browser Download/Upload
```

**不要使用终端复制粘贴配置文件内容。**

如果重新下载原始 `.cfg` 后中文正常，说明原文件无问题。

---

### 方案 B：尝试抢救已经乱码的文件

如果原始文件已经找不到，可尝试修复。

先备份：
```bash
cp A-su-cs-ztlig.cfg A-su-cs-ztlig.cfg.bad.bak
```

尝试 Latin1 反转：
```bash
python3 << 'PYEOF'
from pathlib import Path

src = Path("A-su-cs-ztlig.cfg")
dst = Path("A-su-cs-ztlig.fixed.cfg")

text = src.read_text(encoding="utf-8", errors="replace")
fixed = text.encode("latin1", errors="ignore").decode("utf-8", errors="replace")

dst.write_text(fixed, encoding="utf-8")
print("已生成:", dst)
PYEOF
```

查看效果：
```bash
nl -ba A-su-cs-ztlig.fixed.cfg | head -30
```

如果恢复正常，覆盖原文件：
```bash
cp A-su-cs-ztlig.fixed.cfg A-su-cs-ztlig.cfg
```

> 如果乱码中已经出现 `�`，说明部分字节已经丢失，无法 100% 无损恢复。

---

### 方案 C：使用 ftfy 尝试修复

```bash
python3 -m pip install ftfy -i https://pypi.tuna.tsinghua.edu.cn/simple
```

```bash
python3 << 'PYEOF'
from pathlib import Path
from ftfy import fix_text

src = Path("A-su-cs-ztlig.cfg")
dst = Path("A-su-cs-ztlig.ftfy.cfg")

text = src.read_text(encoding="utf-8", errors="replace")
fixed = fix_text(text)

dst.write_text(fixed, encoding="utf-8")
print("已生成:", dst)
PYEOF
```

---

## 六、预防措施

1. **不要通过终端复制粘贴中文配置文件** — 终端复制的是"渲染后的字符"，不是原始文件字节
2. **使用文件传输方式** — scp/sftp/rsync/rz/sz，推荐 MobaXterm 左侧 SFTP Browser
3. **直接在服务器上编辑** — `vim`、`nano`、VS Code Remote SSH
4. **MobaXterm 设 UTF-8** — Settings → Configuration → Terminal → Charset
5. **Windows 编辑器保存前确认编码** — 推荐 VS Code 或 Notepad++，保存为 UTF-8

---

## 七、快速判断口诀

```text
file/enca 说 UTF-8，
locale 也 UTF-8，
echo 中文正常，
但 cat/vim 仍乱码，
多半是内容已经被错误转码后保存。
```

---

## 八、Hermes 执行顺序

当用户反馈 `.cfg` 中文注释乱码时，按以下顺序执行：

```bash
enca <file>
file -i <file>
iconv -f UTF-8 -t UTF-8 <file> -o /dev/null
locale
echo "中文测试"
nl -ba <file> | head -30
```

然后根据结果判断：
- 如果 `echo` 都乱码：查终端/字体/SSH 客户端
- 如果 `echo` 正常、文件合法 UTF-8、但内容类似 `æŽ¥å�£`：判断为二次乱码
- 如果重新获取原始文件后正常：确认根因是复制粘贴链路损坏
- 优先建议重新传原文件，而不是盲目 `iconv` 转码

## 典型乱码对照表

| 显示内容 | 原始中文 | 错误编码 |
|---------|---------|---------|
| `æŽ¥å�£` | 接口 | UTF-8 → Latin1 |
| `ä½¿ç”¨` | 使用 | UTF-8 → Latin1 |
| `æ¨¡å�—` | 模块 | UTF-8 → Latin1 |
| `ã€�` | 空格/引号类 | UTF-8 → CP1252/Latin1 |

## 参考案例

`references/moba-zte-cfg-case.md` — 中兴 ZTE LIG 配置文件实际乱码案例
