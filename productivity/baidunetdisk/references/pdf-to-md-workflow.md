# PDF → Markdown 转换工作流（华为LI技术文档实战）

本文件记录了将百度网盘中的华为合法监听技术 PDF 转换为可搜索 Markdown 的完整过程。

## 工具选型

| 工具 | 安装 | 依赖 | 质量 | 适用场景 |
|------|------|------|------|----------|
| **markitdown** (Microsoft) | `pip install markitdown[pdf]` | 轻量，无需 GPU | 中 | 技术文档、表格页面 |
| marker-pdf (datalab-to) | `pip install marker-pdf` | PyTorch + surya (GPU推荐) | 高 | 复杂排版、学术论文 |
| pdf2md (npm) | `npx pdf2md file.pdf output` | Node.js | 低 | 只转每页为图片嵌入 |

推荐: Microsoft MarkItDown。安装简单，无需 GPU。

## 安装

```bash
pip install markitdown[pdf] --break-system-packages
pip install markitdown[docx]    # 用于转换 3GPP 规范的 .docx 源文件
```

## 使用

```bash
markitdown input.pdf > output.md
markitdown input.docx > output.md   # 也支持 docx
```

## DOC 格式转换

3GPP 规范早期版本使用 .doc 格式（非 .docx），需先转换：
```bash
libreoffice --headless --convert-to docx xxx.doc
markitdown xxx.docx > xxx.md
```

## 华为LI文档实战效果

| PDF | 大小 | Markdown行数 | 关键内容 |
|-----|------|-------------|----------|
| HW_NGN_X1X2.pdf | 737KB | 2045行 | X1/X2帧结构、C命令码表 |
| LI-HW.pdf | 2.3MB | 14125行 | CS ETSI规范+第12章ASN.1 PER语法 |
| NGN_XPTU.pdf | 2.1MB | ~5400行 | XPTU接口参数定义 |

## 3GPP 规范转换

3GPP 规范通过 FTP ZIP 下载，内含 .docx 源文件 + ASN.1 附件：
```bash
curl -LO "https://www.3gpp.org/ftp/Specs/archive/33_series/33.108/33108-i00.zip"
unzip 33108-i00.zip
unzip 33108-i00-attachments.zip -d asn1/
markitdown 33108-i00.docx > ts33108.md
```
详见 `references/3gpp-spec-download-and-convert.md`

### LI文档分析工作流（参考hw-li-x1-protocol-knowledge.md）

1. xpan API扫描网盘 → 找到LI-STAND目录中的PDF
2. 通过xpan multimedia接口获取dlink下载
3. markitdown转换为md →
4. 存入~/knowledge/baidu-netdisk/parsed/
5. 手动提取ASN.1章节(第12章)、NE type表(Table 2-2)、X1帧头定义(2.1节)
6. 整理到references/hw-li-x1-protocol-knowledge.md

### 解析关键位置指引

PDF中的ASN.1语法和协议表可能不是标准Markdown可提取的纯文本，需要：
- LI-HW.pdf ASN.1章节: 文本提取(markitdown)后约在10368~11332行之间
- 华为NGN版帧结构: 在HW_NGN_X1X2.pdf文本提取的182~197行附近(txzdef struct X1Frame)
- NE type表: LI-HW.pdf提取文本的826~852行(Table 2-2)
- CS vs IMS差异: 680~748行(1.3节)
- X2-X3关联: 8735~8814行(4.3节)

### ASN.1 关键位置（LI-HW.md）
- Chapter 12 Appendix D — X1 DEFINITIONS IMPLICIT TAGS
- 12.1 X1 消息类型 30 种 CHOICE
- 12.2 X2 IRI 上报 ASN.1
- PERALIGN: ALIGN, ENDIAN: BIG

### 转换质量注意事项
1. 表格线可能错位，需手动校对
2. PDF中嵌入的图片不提取
3. 代码块（C struct/ASN.1）缩进可能变形
4. 英文技术文档质量高于中文混合文档

转换后保存到 ~/knowledge/baidu-netdisk/parsed/
