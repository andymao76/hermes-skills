# 6 个初始提取失败的 CHM 恢复记录

**日期：** 2026-06-17
**工具链：** 7z + iconv + html2text
**初始失败原因：** 脚本搜索 `.html` 而非 `.htm`，6 个 CHM 全部产出空壳文件

## 恢复结果对比

| CHM 文件 | 原始大小 | 修复前 | 修复后 | 修复方法 |
|----------|:--------:|:------:|:------:|----------|
| 国内无线核心网G9 | 208K | 310B (空壳) | 5.7KB | 改搜 .htm + gb2312 |
| 国内G9新建工程问题汇总 | 519K | 292B (空壳) | 1.5KB | 改搜 .htm（大部分图片） |
| 无线核心网MSC维护手册 | 1.5MB | 312B (空壳) | **1.6MB** | 改搜 .htm + 43 页面全部转换 |
| CGP 维护宝典 V3.1.3 | 4.5MB | 196B (空壳) | **43KB→337KB** | 先改搜 .htm（43KB/1页），再换 html2text（337KB/158页） |
| USN9810 跟踪解析插件 | 407K | 230B (空壳) | **26KB** | 改搜 .htm + 21 页面全部转换 |
| MSOFTX3000 V100R007C03 | 4.0MB | 218B (空壳) | **2.0MB** | 改搜 .htm + 43/618 页面转换 |

## 关键教训

### 1. 搜索文件时必须同时匹配 `.htm` 和 `.html`

```bash
# ❌ 错误 — 会漏掉 CHM 的 HTM 文件
find . -name "*.html" -type f

# ✅ 正确 — 两种扩展名都要搜索
find . \( -name "*.htm" -o -name "*.html" \) -type f
```

### 2. 多编码 fallback 策略

Word HTML 格式 CHM 通常为 gb2312 编码。推荐依次尝试：

```bash
for enc in gb2312 gbk gb18030 utf-8; do
  content=$(iconv -f "$enc" -t utf-8 "$f" 2>/dev/null | html2text --body-width=0 2>/dev/null)
  [ -n "$content" ] && [ ${#content} -gt 50 ] && break
done
```

### 3. pandoc vs html2text 的选择标准

- **标准 HTML 页面** → pandoc（表格渲染更好）
- **Word HTML（含 xmlns:vml / mso-* 属性）** → 必须用 `html2text`
- 判断方法：`grep -q 'xmlns:w="urn:schemas-microsoft-com:office:word"' page.htm`

## 完整批量提取命令

```bash
#!/bin/bash
CHM_DIR="$HOME/chm"
OUT_DIR="$HOME/knowledge/li/imported"

for chm in "$CHM_DIR"/*.chm; do
  base=$(basename "$chm" .chm | sed 's/[[:space:]]/_/g; s/(//g; s/)//g')
  tmp="/tmp/chm_extract/${base}"
  rm -rf "$tmp"
  mkdir -p "$tmp" "$OUT_DIR"
  
  7z x "$chm" -o"$tmp" -y > /dev/null 2>&1
  
  # 关键：搜索 .htm 和 .html
  htmls=$(find "$tmp" \( -name "*.htm" -o -name "*.html" \) -type f | sort)
  
  {
    echo "---"
    echo "title: ${base}"
    echo "source: CHM: $(basename "$chm")"
    echo "extracted: $(date +%Y-%m-%d)"
    echo "tags: [chm-import]"
    echo "---"
    echo ""
  } > "$OUT_DIR/${base}.md"
  
  for html in $htmls; do
    rel="${html#$tmp/}"
    [[ "$rel" == *".hhc" ]] && continue
    [[ "$rel" == *".hhk" ]] && continue
    
    # 多编码尝试
    md=""
    for enc in gb2312 gbk gb18030 utf-8; do
      md=$(iconv -f "$enc" -t utf-8 "$html" 2>/dev/null | html2text --body-width=0 --ignore-links --ignore-images 2>/dev/null)
      [ -n "$md" ] && [ ${#md} -gt 50 ] && break
      md=""
    done
    
    if [ -n "$md" ] && [ ${#md} -gt 50 ]; then
      echo -e "\n---\n### ${rel}\n" >> "$OUT_DIR/${base}.md"
      echo "$md" >> "$OUT_DIR/${base}.md"
    fi
  done
  
  rm -rf "$tmp"
done
```
