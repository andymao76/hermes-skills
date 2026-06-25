# 百度网盘文档下载与内容分析工作流

## 流程

1. **xpan list** → 获取目录下文件清单（含 fs_id, size）
2. **xpan filemetas** → 用 fs_id 获取 dlink（直链下载地址）
3. **下载** → dlink + access_token 作为 URL 参数
4. **PDF 文本提取** → `pdftotext input.pdf output.txt`
5. **grep 搜索** → 在文本中查找关键术语
6. **分析** → 从 PDF 文本中提取结构化信息

## 成功实践的案例

本技能目录下的 `files/` 包含了从百度网盘 `/LI-STAND/` 下载的关键 LI 文档：

- `HW_NGN_X1X2.pdf` (737KB) — 华为 NGN X1/X2 接口协议，含完整的 X1 帧结构定义和命令码表
- `LI-HW.pdf` (2.3MB) — 华为 CS 域合法监听 X 接口规范，含第12章 ASN.1 语法描述
- `NGN_XPTU.pdf` (2.1MB) — NGN XPTU 接口说明

## 坑

- `pdftotext` 对格式化的表格/图表/ASN.1 定义提取效果差，文本容易混乱
- `read_file` 不能读 PDF 文件（报错），必须先用 `pdftotext` 转 TXT
- PDF 文本中的页码、页脚、页眉会干扰 grep 搜索
