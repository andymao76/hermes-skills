# CHM 文档提取入库工作流

> 适用场景：需要将 CHM（Compiled HTML Help）格式的技术文档提取为 Markdown 并存入知识库。

## 前置条件

| 工具 | 用途 | 安装 |
|------|------|------|
| `7z` (p7zip) | 解压 CHM 文件（CHM 本质是一个 ITSF 压缩包） | `apt install p7zip-full` |
| `iconv` | 编码转换（CHM 常用 gb2312） | 系统自带 |
| `pandoc` | HTML → Markdown 转换 | `apt install pandoc` |

## 工作流

### 1. 解压 CHM

```bash
7z x "文档.chm" -o/tmp/chm_extract/文档名 -y
```

CHM 会解压出 HTML 文件、索引文件（.hhc/.hhk）和资源目录。

### 2. 跳过非内容文件

排除目录索引文件：
- `.hhc` — 目录表
- `.hhk` — 关键词索引
- `#ITBITS`, `$FIftiMain` 等 CHM 内部结构文件

### 3. 编码转换 + HTML→Markdown

CHM 中 HTML 通常使用 gb2312 编码，需先转 UTF-8 再转换：

```bash
iconv -f gb2312 -t utf-8 "page.html" | pandoc -f html -t markdown --wrap=none
```

### 4. 多文件合并

一个 CHM 包含多个 HTML 页面（从几十到几千不等），用 `---` 分隔并标注源路径：

```markdown
---
### relative/path/to/page.html
---
```

### 5. 入库

根据内容类型选择目录：
- 电信/LI 相关 → `~/knowledge/li/imported/`
- 公开技术 → `~/knowledge/telecom/` 或 `~/knowledge/技能/`
- 处理完后建议执行 `enzyme refresh` 更新语义索引

## 批量处理脚本模板

```bash
#!/bin/bash
# 批量提取 CHM 入库
CHM_DIR="$HOME/chm"
OUT_DIR="$HOME/knowledge/li/imported"

for chm in "$CHM_DIR"/*.chm; do
  base=$(basename "$chm" .chm | sed 's/[[:space:]]/_/g; s/(//g; s/)//g')
  tmp="/tmp/chm_extract/${base}"
  mkdir -p "$tmp" "$OUT_DIR"
  
  7z x "$chm" -o"$tmp" -y > /dev/null 2>&1
  htmls=$(find "$tmp" -name "*.html" -type f | sort)
  
  # 写 YAML frontmatter
  {
    echo "---"
    echo "title: $base"
    echo "source: CHM: $(basename "$chm")"
    echo "extracted: $(date +%Y-%m-%d)"
    echo "tags: [chm-import]"
    echo "---"
  } > "$OUT_DIR/${base}.md"
  
  for html in $htmls; do
    rel="${html#$tmp/}"
    [[ "$rel" == *".hhc" ]] && continue
    [[ "$rel" == *".hhk" ]] && continue
    
    md=$(iconv -f gb2312 -t utf-8 "$html" 2>/dev/null | pandoc -f html -t markdown --wrap=none 2>/dev/null)
    if [ -n "$md" ] && [ ${#md} -gt 100 ]; then
      echo -e "\n---\n### ${rel}\n" >> "$OUT_DIR/${base}.md"
      echo "$md" >> "$OUT_DIR/${base}.md"
    fi
  done
  rm -rf "$tmp"
done
```

## 已知问题

| 问题 | 原因 | 处理 |
|------|------|------|
| 部分 CHM 解压后 HTML 无内容 | CHM 使用非标准压缩或加密 | 跳过，仅保留 frontmatter |
| gb2312 转码乱码 | HTML 声明编码与实际不一致 | 尝试 `iconv -f gbk` 或 `-f gb18030` |
| 超大 CHM（>50MB）转换慢 | HTML 文件数千页 | 单独处理，设置超时 600s |

## 本工作流产生的文件

首次批量提取（2026-06-17）：`~/knowledge/li/imported/` 下 18 个文件，84MB，涵盖：
- ME60 产品文档/日志参考（35MB+13MB+8.5MB）
- PS Solution CSFB/VoLTE（13MB+6.9MB）
- GPRS/UMTS/GGSN 信令分析（4.1MB+2.1MB）
- LI ETSI/LICI 监听搭建文档
- MSOFTX3000 号码分析
- Wireshark 中文用户手册
- ZXR10 交换机命令参考
