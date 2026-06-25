# CGP 维护宝典 V3.1.3 批量提取实战记录

**日期：** 2026-06-17
**工具链：** 7z + iconv + html2text
**CHM 文件：** CGP 维护宝典V3.1.3.chm（4.5MB, 158 HTM 文件）
**产出：** ~/knowledge/li/imported/CGP_维护宝典V3.1.3.md（337KB）

## 关键发现

1. **文件扩展名是 `.htm` 而非 `.html`** — 初始脚本用 `.html` 过滤，158 个文件只抓到 1 个
2. **Word HTML 格式 pandoc 无法解析** — 第一版 158 个文件只转了 1 个（43KB）。改用 `html2text` 后 158/158 全部成功（337KB）
3. **gb2312 编码** — 需 `iconv -f gb2312 -t utf-8` 先转码再喂给 html2text

## 成功提取的内容结构

| 大类 | 子项 | 文件数 |
|------|------|:------:|
| 01 信息收集指导 | CGA/CGP 信息收集，12 种定位手段，16 类故障信息，VTS 工具 | 30 |
| 02 案例库 | 9 大类 87 个实战案例（系统安装/LMT/WEBUI/网管/告警/性能/OMU监听/主机/VTS） | 117 |
| 03 FAQ | 10 类日常运维问答 | 10 |
| 附录 | 版本新增案例清单、版本配套关系表 | 3 |

## 关联知识库中的其他版本

`~/knowledge/li/lawful_interception/华为CGP维护宝典.md` — 从同一 CHM 手动录入的早期版本，内容结构略有不同但涵盖相同主题。

## 批量提取脚本（bash）

```bash
#!/bin/bash
CHM="$HOME/chm/CGP 维护宝典V3.1.3.chm"
OUT="$HOME/knowledge/li/imported/CGP_维护宝典V3.1.3.md"
TMP="/tmp/cgp_redux"

rm -rf "$TMP" && mkdir -p "$TMP"
7z x "$CHM" -o"$TMP" -y > /dev/null 2>&1

mapfile -t htm_files < <(find "$TMP" -name "*.htm" -type f | sort)
total=${#htm_files[@]}

# YAML frontmatter
{
  echo "---"
  echo "title: CGP_维护宝典V3.1.3"
  echo "source: CHM: CGP 维护宝典V3.1.3.chm"
  echo "extracted: $(date +%Y-%m-%d)"
  echo "tags: [chm-import, huawei, cgp, telecom, lawful-intercept]"
  echo "---"
  echo ""
  echo "# CGP 维护宝典 V3.1.3"
  echo ""
} > "$OUT"

conv=0
for ((i=0; i<total; i++)); do
  f="${htm_files[$i]}"
  rel="${f#$TMP/}"
  [[ "$rel" == *".hhc" ]] && continue; [[ "$rel" == *".hhk" ]] && continue
  
  md=$(iconv -f gb2312 -t utf-8 "$f" 2>/dev/null | html2text --body-width=0 --ignore-links --ignore-images 2>/dev/null)
  
  if [ -n "$md" ] && [ ${#md} -gt 30 ]; then
    echo -e "\n---\n## ${rel}\n" >> "$OUT"
    echo "$md" >> "$OUT"
    conv=$((conv+1))
  fi
done

echo "Done: $total HTM, $conv converted"
rm -rf "$TMP"
```
