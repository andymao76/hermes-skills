# 第二次百度网盘导入实录（2026-06-07）

## 环境状态

| 组件 | 状态 |
|------|------|
| BaiduPCS-Go | 已安装 v4.0.1 |
| bypy | 已安装并授权 |
| pandoc | 已安装 |
| pdftotext | 已安装 |
| LibreOffice | 已安装 |
| `baidupan_convert.py` | 已存在，后续修改了超时和 FTS5 优化 |

## 百度网盘下载目录结构

```
~/baidupan_docs/
├── 364769201_andymao76/    # BaiduPCS-Go 下载主目录（530 个文件）
│   ├── 3GPP-TS/            # 52 个可转换文件（3GPP 协议）
│   ├── 3GPP R15 38系列/    # 全部是 .zip，需解压
│   ├── 5g/                 # 134 个可转换文件
│   ├── 通信电子书籍/       # 62 个可转换文件（ATCA/PICMG 等）
│   ├── EPC核心网资料/      # 55 个可转换文件
│   ├── IMS/                # 17 个可转换文件
│   ├── SIP-PCAP/           # 2 个 .pcap 二进制文件
│   ├── VOLTE/              # 19 个可转换文件
│   └── … 
├── xiaosai/                # 另一个 BaiduPCS 下载（40 个文件）
│   └── 364769201_andymao76/
│       ├── 000000小赛知识库文件/    # ET 工作文件
│       ├── sip协议详解中文版/       # SIP 协议
│       └── VOLTE案例篇汇集/         # VoLTE 案例
```

## 文件类型分布（主目录 530 个文件）

pdf: 243, zip: 67, doc: 66, ppt: 33, docx: 30, pptx: 22, spr: 14, rar: 11, xlsx: 9, txt: 6, xls: 4, state: 4, spd: 4, sdt: 3, pcap: 2, sbk: 2, ssy: 2, sdtfiles: 2, ini: 2, 7z: 2, mht: 1, jpg: 1

## 转换遇到的坑

### 1. LibreOffice 大 .doc 文件超时
- 17MB 的 `25331-4k0-RRC Protocol.doc` 和 11MB 的 `MAP-29002-3k0.doc` 反复导致 LibreOffice 120s 超时
- 解决方法：排除文件后把脚本 timeout 从 120 改为 300 秒
- 遗留问题：这两个文件处理后依然超时（17MB 的 .doc 可能需要手动转换）

### 2. LibreOffice 僵尸进程
- 超时的 LibreOffice 会在后台留 soffice.bin 进程
- 如果不清理，下次转换依然挂死在同一个文件
- 检查：`ps aux | grep -E "libre|soffice" | grep -v grep`

### 3. FTS5 索引超时验证
- 知识库 400+ 文件后，FTS5 因多次 rebuild 未 optimize，搜索超时 30s
- 修复：重建索引后执行 `INSERT INTO knowledge_fts(knowledge_fts) VALUES('optimize')`
- 优化后 178 条 3GPP 结果 0ms 返回

## 最终知识库状态

| 目录 | 文件数 | 大小 |
|------|:------:|:----:|
| articles_baidu/ | 376 | 49 MB |
| research/ | 15 | 9.4 MB |
| notes/ | 5 | 48 KB |
| articles/ | 3 | 56 KB |
| daily/ | 1 | 8 KB |
| **总计** | **400** | **59 MB** |

## 脚本修改记录

`~/.hermes/scripts/baidupan_convert.py`:
1. LibreOffice timeout 120 → 300 秒（大 .doc 文件）
2. `rebuild_fts5_index()` 新增 FTS5 optimize 步骤
3. 以上修改已于本会话完成
