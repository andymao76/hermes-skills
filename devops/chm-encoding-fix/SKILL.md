---
name: chm-encoding-fix
description: 解决 CHM 文件编码非标准导致 pandoc 无法解析的问题 — 反编译 → 编码检测 → 转 UTF-8 → 修复 charset → 修复 HTML → pandoc 转换
---

# CHM 编码修复与转换

当 CHM 文件编码非标准（GB2312/GBK/BIG5/Windows-1252 等）时，pandoc 直接读 .chm 失败。正确做法：先反编译 CHM，修复 HTML 编码，再交给 pandoc。

## 触发条件

- 用户需要转换 CHM 文件但不成功
- pandoc 读 .chm 报编码错误或乱码
- 需要从 CHM 提取内容转 docx/md/pdf

## 完整工作流

### 0. 安装依赖

**推荐方案：7z（无需 sudo，优先使用）**
```bash
which 7z || sudo apt install p7zip-full
```

**备用方案：extract_chmLib（需 sudo，处理 LZX 压缩 CHM）**
```bash
sudo apt install libchm-bin
```

**编码检测与转换：**
```bash
# 推荐：Python charset_normalizer（无需 sudo）
pip install charset-normalizer

# 或：uchardet（需 sudo）
sudo apt install uchardet

# iconv 和 tidy（按需安装）
which iconv || sudo apt install iconv
which tidy  || sudo apt install tidy
```

> 实际执行经验（2026-06-17, 28个CHM批量处理）：
> - **7z** 解压绝大多数 CHM 均成功（华为/中兴/ETSI文档）
> - **charset_normalizer** (Python) 比 uchardet 更易获取、检测更准确
> - **tidy** 在大规模（30K+文件）场景下可选，非必需
> - **iconv** 通常已内置，无需安装

### 2. 反编译 CHM

**方案 A（extract_chmLib）：**
```bash
mkdir -p chm_out
extract_chmLib input.chm chm_out/
```

**方案 B（7z，无需 sudo）：**
```bash
mkdir -p chm_out
7z x input.chm -ochm_out/ -y
```

备选工具：

```bash
# 或使用 archmage（Python 工具）
pip install archmage
archmage input.chm chm_out/
```

> ⚠️ **关键陷阱：CHM 文件可能使用 `.htm` 而非 `.html` 扩展名**
> 搜索 CHM 解压出的 HTML 文件时，必须同时匹配两种扩展名：
> ```bash
> find chm_out -type f \( -name "*.html" -o -name "*.htm" \)
> ```
> 只搜索 `.html` 会漏掉大量实际内容文件，导致输出为空或只有索引框架。

### 3. 检测 HTML 文件编码

**方案 A（uchardet，需 sudo）：**
```bash
find chm_out -type f \( -name "*.html" -o -name "*.htm" \) \
  -exec uchardet {} \;
```

**方案 B（Python charset_normalizer，推荐，无需 sudo）：**
```python
pip install charset-normalizer
python3 -c "
import charset_normalizer, glob, json
encs = {}
for f in glob.glob('chm_out/**/*.htm', recursive=True) + glob.glob('chm_out/**/*.html', recursive=True):
    cn = charset_normalizer.from_bytes(open(f, 'rb').read(4096))
    if cn.best(): encs[cn.best().encoding] = encs.get(cn.best().encoding, 0) + 1
print(json.dumps(encs, ensure_ascii=False, indent=2))
"
```

常见非标准编码：

| 编码 | 常见场景 |
|------|----------|
| GB2312 / GBK | 简体中文 Windows 帮助 |
| BIG5 | 繁体中文 |
| Windows-1252 | 西欧语言早期 CHM |
| ISO-8859-1 | 西欧语言 |
| Shift_JIS | 日文 |

### 4. 批量转 UTF-8

假设检测到原编码是 GBK：

```bash
find chm_out -type f \( -name "*.html" -o -name "*.htm" \) -print0 |
while IFS= read -r -d '' f; do
  iconv -f GBK -t UTF-8 "$f" -o "$f.utf8" && mv "$f.utf8" "$f"
done
```

不确定编码时先单文件测试：

```bash
iconv -f GBK -t UTF-8 page.htm -o page_utf8.htm
```

**多编码尝试（推荐，无需 pre-detect 编码）：**

当编码不确定时，依次尝试多种编码直到成功：

```bash
for enc in gb2312 gbk gb18030 utf-8; do
  content=$(iconv -f "$enc" -t utf-8 page.htm 2>/dev/null | pandoc -f html -t markdown 2>/dev/null)
  if [ -n "$content" ] && [ ${#content} -gt 50 ]; then
    break
  fi
done
```

> **注意**：编码名要匹配 `iconv -l` 列表。如果 `uchardet` 输出 `GB2312`，但 `iconv -f GB2312` 报错，试 `GBK`。`gb18030` 可作为最后保底编码（覆盖 GBK 的所有字符）。

### 5. 修复 HTML charset 声明

很多 CHM 失败是因为内容已转 UTF-8 但 HTML 头里还写着旧编码。

```bash
find chm_out -type f \( -name "*.html" -o -name "*.htm" \) -print0 |
xargs -0 sed -i -E 's/charset=["'\'' ]?[^"'\'' >]+/charset=UTF-8/Ig'
```

或直接插入正确声明：

```bash
find chm_out -type f \( -name "*.html" -o -name "*.htm" \) -print0 |
while IFS= read -r -d '' f; do
  if ! grep -qi '<meta.*charset' "$f"; then
    sed -i '1s/^/<meta charset="UTF-8">\n/' "$f"
  fi
done
```

### 6. 修复脏 HTML（可选，pandoc 仍失败时执行）

```bash
find chm_out -type f \( -name "*.html" -o -name "*.htm" \) -print0 |
while IFS= read -r -d '' f; do
  tidy -utf8 -q -m "$f" 2>/dev/null || true
done
```

### 7. pandoc 转换（标准 HTML 格式）

转 docx：

```bash
pandoc chm_out/index.html -f html -t docx -o output.docx
```

转 markdown：

```bash
pandoc chm_out/index.html -f html -t markdown -o output.md
```

批量合并多文件（如果有多个 htm）：

```bash
pandoc chm_out/*.html -f html -t markdown -o output.md
```

### 7B. html2text 转换（Word HTML / MHTML 格式专用）

当 CHM 源文件由 **Microsoft Word 生成**（HTML 头包含 `xmlns:w=\"urn:schemas-microsoft-com:office:word\"` 或 `mso-*` 属性）时，pandoc 往往只能提取 < 1% 的内容。此时改用 `html2text`：

```bash
# 单文件转换
iconv -f gb2312 -t utf-8 page.htm | html2text --body-width=0 --ignore-links --ignore-images

# 批量转换（推荐）
find chm_out -name \"*.htm\" -type f | sort | while read f; do
  rel=\"${f#chm_out/}\"
  md=$(iconv -f gb2312 -t utf-8 \"$f\" 2>/dev/null | html2text --body-width=0 --ignore-links --ignore-images 2>/dev/null)
  if [ -n \"$md\" ] && [ ${#md} -gt 30 ]; then
    echo -e \"\\n---\\n## ${rel}\\n\" >> output.md
    echo \"$md\" >> output.md
  fi
done
```

**pandoc vs html2text 对比：**

| 对比项 | pandoc | html2text |
|--------|--------|-----------|
| 标准 HTML | ✅ 优 | ✅ 可接受 |
| **Word HTML (mso-* / VML)** | ❌ 通常只转 0-3% | ✅ **100% 成功** |
| 表格渲染 | ✅ 好（markdown 表格） | ✅ 好 |
| 图片引用 | ⚠️ 需额外处理 | ⚠️ --ignore-images 可跳过 |
| 编码兼容性 | 依赖 HTML charset 声明 | 依赖输入流编码（需先 iconv） |

## 批量提取与入库工作流

当需要从多个 CHM 文件批量提取并合并为结构化 Markdown 知识库时：

### 核心逻辑

```
for each .chm:
  1. 7z x → 解压到临时目录
  2. find .htm + .html → 列出所有页面
  3. 对每个 HTM 文件：
     a. 尝试 iconv -f gb2312 → 若失败，依次试 gbk / gb18030 / utf-8
     b. pandoc -f html -t markdown → 转换
     c. 过滤掉 <50 字符的无效页面
  4. 合并写入一个 .md 文件（含 YAML 源信息）
```

### 关键细节

| 项 | 说明 |
|----|------|
| 文件扩展名 | **必须同时搜索 `.htm` 和 `.html`**，CHM 常用 `.htm` |
| 编码探测 | 优先 gb2312 → gbk → gb18030 → utf-8 多路尝试 |
| 内容过滤 | 跳过 `< 50 字符` 的空页面（索引框架、空白页） |
| 文件命名 | 参考 `/tmp/chm_fix_extract.sh` - 完整的批量处理脚本 |
| 元数据 | 每个输出 .md 文件头部插入 YAML frontmatter（源 CHM 名、提取日期、标签） |

## 大规模批量处理（1000+ HTML 文件）

当 CHM 包含数千甚至数万个 HTML 文件（如华为 ME60 设备手册达 33,014 个文件）时，直接全量处理会超时。推荐采样策略：

### 采样检测编码（而非全量扫描）

```python
# 只采样前 50 个文件检测编码，大幅提速
sample_size = min(50, len(html_files))
encodings_found = {}
for html_path in html_files[:sample_size]:
    raw = open(html_path, 'rb').read(4096)
    cn = charset_normalizer.from_bytes(raw)
    if cn.best():
        enc = cn.best().encoding
        encodings_found[enc] = encodings_found.get(enc, 0) + 1
dominant = max(encodings_found, key=encodings_found.get)
```

### Pandoc 只转入口页

对于 30K+ 文件的大型 CHM，pandoc 转换 index.html 就够（入口页包含目录框架），独立页面已在批量编码修复中归一化为 UTF-8。

```bash
# 入口页自动识别顺序
for name in index.html index.htm default.html default.htm table_of_contents.html; do
  [ -f "chm_out/$name" ] && pandoc "chm_out/$name" -f html -t markdown -o output.md && break
done
```

### iconv 批量转换 + 跳过已 UTF-8

```bash
find chm_out -type f \( -name "*.htm" -o -name "*.html" \) -print0 |
while IFS= read -r -d '' f; do
  # 跳过已是 UTF-8 的文件
  if iconv -f UTF-8 -t UTF-8 "$f" >/dev/null 2>&1; then
    continue
  fi
  iconv -f GBK -t UTF-8 "$f" -o "$f.utf8" && mv "$f.utf8" "$f"
done
```

> ⚠️ **大规模处理经验**（2026-06-17, 28个CHM实际执行）：
> - ME60 V800R012C00SPC300: **33,014 个 HTML**, 含 28 种编码（GBK/cp1250/mac_iceland/SHIFT_JIS/hp_roman8...），167MB CHM → 全部 iconv 转 UTF-8 成功
> - 单文件 iconv 时间极短（<10ms），但 30K+ 文件的 find+loop 总耗时约 2-3 分钟
> - charset_normalizer 检测到的 "杂编码"（mac_greek, hp_roman8, ptcp154 等）多来自 HTML 中的二进制元数据或注释，实际正文为 GBK，用 iconv GBK 处理即可
> - 处理超时（300s+）原因通常是：find 遍历 30K 文件 + 逐个 iconv + 逐个 charset 修复 + pandoc，建议分阶段执行

## 处理框架性 CHM（frameset）

华为/中兴等大型设备手册的 CHM 使用 frameset 框架结构：
- `index.html` / `default.html` — 导航框架（很小，pandoc 输出仅 0-3KB）
- 各章节页面 — 独立 `.htm` 文件

**现象**：pandoc 转 index.html 只得到导航目录 + 几个粗链接，正文内容缺失。

**解决方法**：直接转换所有 `.htm` 文件合并（或按需选择主题）：

```bash
find chm_out -name "*.htm" -type f | sort | while read f; do
  rel="${f#chm_out/}"
  [[ "$rel" == *.hhc || "$rel" == *.hhk || "$rel" == "#"* ]] && continue
  md=$(pandoc "$f" -f html -t markdown --quiet 2>/dev/null)
  [ -n "$md" ] && [ ${#md} -gt 50 ] && echo -e "\\n---\\n## ${rel}\\n\\n$md" >> output.md
done
```

1. **`uchardet` 输出 `GB2312` 但 `iconv` 报错** → 用 `GBK` 代替，GBK 是 GB2312 的超集
2. **HTML 编码声明与实际编码不一致** → 必做第 5 步，否则 pandoc 按错的声明解读
3. **CHM 有索引框架（frameset）** → 找 `index.html` 或 `default.html` 作为入口，或直接转换 `*.html`
4. **解包后中文文件名乱码** → 先用 `convmv` 修复文件名或直接用通配符
5. **`tidy` 破坏了中文内容** → 确认加了 `-utf8` 参数
6. **Word HTML 格式 pandoc 只转 1 页** → 改用 `html2text`（见 7B 节），pandoc 无法解析 Microsoft Word VML/WordML 命名空间
7. **7z 解压后没有 .htm/.html 文件** → CHM 内容存储在 `#ITBITS` 压缩流中，7z 无法解压此流。需安装 `libchm-bin`（`extract_chmLib`）才能正确反编译

## 验证清单

- [ ] CHM 成功反编译到目录
- [ ] HTML 文件编码统一为 UTF-8
- [ ] charset 声明已改为 UTF-8
- [ ] pandoc 转换无编码错误
- [ ] 输出文件内容正常（无乱码）

## 参考文件

- `references/batch-chm-extract-notes.md` — 28 个 CHM 批量提取实战笔记（已知陷阱和工作流）
- `references/cgp-batch-extract-2026-06-17.md` — CGP 维护宝典 V3.1.3 批量提取实战记录
- `references/6-failed-chm-recovery.md` — 6 个初始提取失败的 CHM 文件恢复记录
- `references/batch-28-chm-execution-2026-06-17.md` — 28 个 CHM 第二次完整批量处理记录（含大规模 timeout 处理策略、编码分布统计、frameset 框架处理经验）
