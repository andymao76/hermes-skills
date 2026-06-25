# PDF to Markdown —工具对比实测

## 测试场景

3份华为合法监听规范 PDF:
| 文档 | 页数 | 大小 | 特点 |
|------|------|------|------|
| HW_NGN_X1X2.pdf | 50 | 737KB | 老版NGN协议,C结构体定义,版本修订表 |
| LI-HW.pdf | 259 | 2.3MB | CS ETSI新版,含30种ASN.1 CHOICE定义 |
| NGN_XPTU.pdf | 72 | 2.1MB | 架构描述+ISUP参数表 |

## 工具对比

| 工具 | 安装体积 | 速度 | ASN.1语法 | C结构体表格 | 修订记录表 | HEX码流示例 |
|------|---------|------|-----------|------------|-----------|------------|
| pdftotext (poppler) | ~2MB | 瞬出 | ❌ 行错位 | ❌ 丢失换行 | ❌ 表变乱码 | ❌ 数字堆叠 |
| markitdown[pdf] | ~10MB | ~0.5s/页 | ✅ 完整保留 | ✅ 转为.md表格 | ✅ 转为.md表格 | ✅ 保留十六进制序列 |
| pymupdf | ~25MB | 瞬出 | ⚠️ 文本可提取但表格结构丢失 | ❌ | ❌ | ⚠️ 仅原始文本 |

## 结论

**技术协议文档（ASN.1, C struct, 协议表, HEX码流）→ 用 markitdown[pdf]**

安装:
```bash
pip install markitdown[pdf] --break-system-packages
markitdown doc.pdf > output.md
```

markitdown 在华为LI-HW 259页文档上成功提取了第12章完整的ASN.1 PER定义(30种X1MessageType的CHOICE、每个SEQUENCE的16+字段)，是唯一能正确保留ASN.1语法结构的轻量工具。

## 3GPP规范下载方法

ETSI官方PDF链接经常仅返回重定向页(35KB)。正确方式是通过3GPP FTP:
```
https://www.3gpp.org/ftp/Specs/archive/33_series/33.108/
```
下载 `.zip` 文件，内含:
- `docx` → markitdown 转 md
- `attachments.zip` → 解压得原始 `.asn` ASN.1文件(19个文件覆盖2G-5G)
