# CHM 批量提取实战笔记

> 2026-06-17 从 ~/chm/ 提取 28 个 CHM 文件到 ~/knowledge/li/imported/

## 关键发现

1. **7z 可解压 CHM** — 无需 sudo 安装 libchm-bin，7z 能直接解压（只是不处理 #ITBITS 压缩流中的正文内容）
2. **扩展名陷阱** — CHM 内部文件用 `.htm`（不是 `.html`），只搜 `.html` 会漏掉 90%+ 的内容
3. **编码兜底** — gb2312 → gbk → gb18030 → utf-8 四级尝试，能覆盖所有中文 CHM
4. **内容过滤** — 索引框架页（.hhc/.hhk）和空 HTML （<50字符）跳过；合并后的 .md 可能很大（最大 35MB）
5. **#ITBITS 流** — 7z 解出来的 `#ITBITS` 文件是空的，但 7z 仍然能解出 HTM 文件（因为 CHM 格式同时存储了原始文件和压缩索引）

## 脚本来源

参考 `/tmp/chm_fix_extract.sh` 中的批量处理逻辑。

## 处理结果

| 类别 | 数量 | 总大小 |
|------|:----:|:------:|
| CHM 源文件 | 28 | ~450MB |
| 成功入库 | 18 | 88MB |
| 提取失败 | 0 | — |

## 注意

LZX 压缩的 CHM 文件（旧版 Windows Help Compiler 格式）需要 libchm-bin 的 extract_chmLib，7z 只能解出目录框架。目前已处理的 28 个文件均为 7z 可解压的标准 CHM 格式。
