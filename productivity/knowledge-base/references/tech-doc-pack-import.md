# 技术文档包批量导入知识库

当用户给一个 ZIP 包或目录，内含多份技术文档（docx + ASN.1 + HTML差异 + Tag日志等），按此工作流处理。

## 前置检查

```bash
unzip -l file.zip              # 预览内容
ls -la src_dir/                 # 如果是目录，先看文件清单
```

## ZIP 中文编码处理

Windows 来源的 ZIP 文件名通常是 GBK 编码：

```bash
# ✅ 正确
unzip -O gbk 华为LI标准协议翻译.zip -d output_dir

# ❌ 错误（文件名乱码）
unzip 华为LI标准协议翻译.zip
```

## 文档格式提取

| 源格式 | 命令 | 说明 |
|--------|------|------|
| .docx | `pandoc -t markdown --wrap=none file.docx -o file.md` | 首选方案 |
| .doc | `libreoffice --headless --convert-to docx` → pandoc | 旧版 Word |
| .asn | 直接 `cp` | ASN.1 纯文本 |
| .html (对比) | `pandoc -t plain` 提取可读文本 | 差异对比用 plain 模式 |
| .tag.log | 直接 `cp` 或转 Markdown 表格 | Tag 映射表 |
| .md5 | 直接 `cp` | 校验文件 |

## 内容学习要点

- **docx**：关注架构、接口定义、消息格式、关键参数（X1/X2/X3 的定义、TNEType/FUNCType/LIOID 等）
- **ASN.1**：关注 SEQUENCE 结构、Tag 值分配、CHOICE 分支、IMPLICIT/EXPLICIT TAGS
- **差异对比**：关注两个版本之间新增/删除/修改了什么字段
- **Tag 日志**：提取所有唯一 tags 对应关系，作为解码参考

## 知识库目录结构

```
knowledge/research/<主题名>/
├── 华为5GC_LI协议标准.md     # docx 提取的完整内容
├── 华为CS_LI协议标准.md      # docx 提取的完整内容
├── asn/
│   ├── hw_5gc_x1.asn         # ASN.1 定义
│   └── ...
└── 华为5GC_X2_Tag映射表.md    # Tag 索引参考
knowledge/research/<主题名>.md  # 索引入口文件（YAML frontmatter + 目录 + 概括）
```

## 索引入口文件格式

```yaml
---
title: 华为 LI 标准协议翻译
tags:
  - 华为
  - LI
  - 5GC
  - ASN.1
links:
  - "[[ETSI_3GPP_Lawful_Intercept_Standards]]"
  - "[[相关文档]]"
created: 2026-06-09
source: /原始路径/file.zip
---
```

body 包含：目录结构概览、每个文件的要点、关键发现、关联链接。

## 索引刷新

```bash
cd ~/knowledge && enzyme refresh
```

## 总结输出

一次性输出，用表格+分层结构，覆盖：
1. ZIP/目录包含哪些文件
2. 每个文件的核心内容要点
3. 关键发现（结构差异、编码区别、接口定义关键点）
4. 导入位置

不要分段输出，不要中途问"是否继续"。
