# ETSI-ASN1-Assistant UI & 报告生成模式

## 一、页面架构

| 路由 | 功能 | 设计要点 |
|------|------|---------|
| `/` | HI2 解码 (PCAP/IRI) | 两列布局(PCAP+IRI)，顶部 nav-tab 链接到 /x-interface |
| `/x-interface` | X 接口日志分析 | 独立页面，完整双栏+过滤+统计+报告 |

- **功能页面必须独立**，不要合并到主页面。用户强制要求。
- 顶部 nav-tabs：`📡 HI2 解码`(当前) | `🔬 X 接口日志`(链接)
- 版本号只出现在右上角 badge 和页脚，不在标题文字中。

## 二、PCAP 解码页面

### 核心流程
```
选择 PCAP → 勾选「TCP 重组」→ 输入端口过滤(8890) → 选解码模式 → 上传并解析
```

### UI 规则
- PCAP 提示条必须**缺省可见**（无 display:none），蓝底白字提醒 TCP重组+端口过滤
- 端口过滤标为 **(必选)** 红色标签，输入框蓝色高亮边框
- 端口占位符：`例如: 8890`
- TCP 重组复选框保持在 PCAP 上传框内

### 常见错误提示
```
建议勾选「TCP 重组」并输入端口过滤（如 8890），可大幅减少非 X2 口报文的解码失败
```

## 三、X 接口日志分析页面

### 布局结构
```
┌─ 顶部: 文件选择 + 接口类型 + 分析按钮 ─┐
├─ 统计栏 (5个卡片) ──────────────────────┤
├─ 导出栏 (HTML / Markdown 按钮) ────────┤  ← 仅 ZTLIG 模式显示
├─ 综合分析报告 (可折叠章节) ─────────────┤  ← 四种日志类型
├─ 双栏: 左栏(解析摘要) | 右栏(原始日志) ─┤
├─ 过滤栏 (LIID/CIN/关键词/级别) ─────────┤
└─────────────────────────────────────────┘
```

### 综合分析报告
- **标题动态化**：使用 `r.title`（ZTLIG1/ZTLIG2/SSF/RVF 各自标题）
- **概览标签**：时间范围、总行数、ERROR、LIID
- 类型特有标签：CallID(SIP)、Correlation/RTPSession(RVF)、LigCdr(ZTLIG2)
- **条件渲染**：ZTLIG1 显示子模块/设控停控/网元故障；其他类型不显示
- 关键样本：优先 ZTLIG1 命名样本(kafka_msg/add_success 等)，否则通用 sample_N

### 左栏摘要模式
- 有报告时按命令分组显示（非逐行）
- 每组：命令名 + 次数 + 涉及LIID/NE列表 + 前3条body样本
- 分组顺序：网元通信故障(红色) → 设控/停控(青色) → 其他操作
- 过滤联动：过滤后重新生成摘要

### 导出报告
- `samplesList` 必须在函数级定义（非 if 块内），避免作用域 bug
- HTML 模式：自包含深色主题页面，内嵌样式
- Markdown 模式：表格格式，可用 \`\`\` 代码块展示样本
- Markdown 字符串中的 `\n` 必须用 Python 字符串中的 `'\\n'`（勿写成 `'\\\\n'`）

## 四、后端 API

### /x-interface-analyze 端点
```python
# 输入: content, subtype, interface, filename
# 输出: { parsed, raw, stats, report }

# 报告生成 (所有类型):
report = generate_report(subtype, parsed)
```

### 报告函数
- `generate_report(subtype, parsed)` — 分发到类型特定函数
- `generate_ztlig1_report(parsed)` — 子模块/命令/LIID/设控停控/网元故障/样本
- `generate_ztlig2_report(parsed)` — LIID/EventDetail/LigCdr
- `generate_ssf_report(parsed)` — LIID/SIP方法/CallID
- `generate_rvf_report(parsed)` — LIID/CorrelationID/RTP会话/媒体类型

每个报告返回结构：`{ title, time_range, total_lines, errors, liid_count, top_liids, samples }` + 类型特有字段。

## 五、导出报告 (exportReport)

### 必须检查项
1. `samplesList` 定义在 `exportReport` 函数顶部（if/else 之前），供 HTML 和 Markdown 分支共用
2. 类型特有字段使用可选链：`report.commands?.length`、`report.ne_faults?.link_check`
3. Markdown 字符串使用 `'\\n'`（Python 字符串中写 `\\n` 得到 JS 的 `\n`）
4. 通用样本：先检查命名 key(kafka_msg 等)，没有则用 Object.keys 遍历

## 六、常见 Bug

| Bug | 根因 | 修复 |
|-----|------|------|
| 导出按钮无反应 | `const samples` 定义在 HTML if 块内，Markdown else 块无法访问 | 改为函数级 `samplesList` |
| Markdown 输出文字 `\n` | `\\\\n` 写成了双反斜杠 | 使用 `'\\n'` |
| 报告标题空白 | `generate_ztlig1_report` 返回 dict 缺 `title` 字段 | 添加 `"title"` |
