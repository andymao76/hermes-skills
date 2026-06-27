---
name: x-interface-log-analysis
title: "X 接口日志分析工具开发"
description: "ETSI-ASN1-Assistant V4 X接口日志分析功能的开发指南 — 覆盖ZTLIG1/ZTLIG2/SSF/RVF四种日志类型的解析、报告生成、大文件处理、前端UI/UX模式"
version: "v1.0"
date: "2026-06-28"
author: "Hermes Agent"
---

# X 接口日志分析工具开发

ETSI-ASN1-Assistant V4 的 X 接口日志分析功能（`/x-interface` 页面）。覆盖 ZTLIG1/X1、ZTLIG2/X2、SSF/SIP、RVF/RTP 四种日志类型的解析与报告生成。

## 触发条件

当用户要求修改、扩展、调试或重构 X 接口日志分析功能时加载此 skill。

## 架构

```
前端 x_interface.html       后端 app_linux_v4.py
  ├── 上传 + 加载动画          ├── /x-interface-analyze API
  ├── 统计栏 (stats-bar)       ├── analysis_time 计时
  ├── 综合分析报告 (report)    └── is_large 大文件模式
  ├── 左栏摘要模式
  └── 右栏原始日志
                              x_interface_decoder.py
                                ├── parse_log_file() 解析
                                ├── generate_summary() 统计
                                └── generate_*_report() 4种报告
```

## 用户偏好的 UI/UX 模式

1. **结论优先** — 显示综合分析报告，而不是原始日志行
2. **摘要模式** — 左栏按命令分组显示关键信息（卡片式），不渲染逐行
3. **关键发现** — 自动生成观察结论，🔍金色标题
4. **带占比** — 统计表显示 `次数 + 占比%` 列
5. **仅 Markdown 导出** — 不要 HTML 导出按钮
6. **手工选择** — 接口类型和子类型全部手工选
7. **加载反馈** — 按钮状态变化 + 中央进度步骤
8. **分析耗时** — 统计栏显示耗时卡片

## 大文件处理

- 前端截断: `file.slice(0, 10MB)`
- 后端全量处理, 无 size 限制
- `is_large=True` 返回报告 + 摘要(5K) + 预览(1K)

## 常见陷阱

1. 用 FileReader 而非 Blob.text() — 兼容性更好
2. 不要在错误处理中引用不存在的函数
3. Markdown 字符串用 `\n` 不是 `\\n`
4. samples 数组要定义在函数级作用域

## 前端关键函数

| 函数 | 作用 |
|------|------|
| showLoading() | 进度动画 |
| analyzeFile() | 读取→上传→展示 |
| displayResults() | 渲染全页面 |
| buildReportHTML() | 报告 HTML |
| buildParsedSummary() | 摘要卡片 |
| exportReport() | Markdown导出 |
