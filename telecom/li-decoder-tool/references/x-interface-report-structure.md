# X 接口日志分析报告结构 (V4.0.1)

## 报告生成架构

后端 `x_interface_decoder.py` 中 `generate_report(subtype, parsed)` 分派到：
- `generate_ztlig1_report()` → ZTLIG1 特有字段
- `generate_ztlig2_report()` → ZTLIG2 特有字段
- `generate_ssf_report()` → SSF 特有字段
- `generate_rvf_report()` → RVF 特有字段

前端 `x_interface.html` 中：
- `displayResults()` 检查 `data.report` 是否存在
- `buildReportHTML(r)` 根据 `r.type`/`r.title` 动态渲染各章节
- `buildParsedSummary(parsed, report)` 按命令分组显示摘要
- `showLoading(name, size)` 显示「⏳分析中...」状态
- 大文件用 `FileReader.readAsText(blob, 'utf-8')` 读取前 10MB
- `.catch(err => alert(...))` 中不调用未定义函数（避免 ReferenceError）

## 报告 JSON 结构

### 通用字段
```json
{
  "title": "报告标题",
  "type": "ztlig1|ztlig2|ssf|rvf",
  "time_range": {"start": "...", "end": "..."},
  "total_lines": 28635,
  "errors": 6,
  "liid_count": 133,
  "top_liids": [{"liid": "10107", "count": 16}, ...]
}
```

### ZTLIG1 特有字段
```json
{
  "sub_modules": [{"name": "ztlig-1_web", "count": 7132, "pct": 71.3}, ...],
  "commands": [{"name": "redis_sync", "count": 3131}, ...],
  "set_target_count": 60,
  "del_target_count": 11,
  "set_liid_count": 13,
  "del_liid_count": 2,
  "ne_faults": {"link_check": 3765, "link_error": 941, "no_response": 468, "top_fault_ne": [...]},
  "samples": {"kafka_msg": "...", "add_success": "...", "ne_response": "...", ...},
  "error_samples": ["..."]
}
```

### ZTLIG2 特有字段
```json
{
  "ligcdr_count": 150,
  "event_detail": [{"name": "10", "count": 50}, ...],
  "network_type": [],
  "vendor": []
}
```

### SSF 特有字段
```json
{
  "sip_methods": [{"name": "200", "count": 5843}, {"name": "INVITE", "count": 3434}, ...],
  "call_id_count": 89
}
```

### RVF 特有字段
```json
{
  "correlation_id_count": 45,
  "rtp_session_count": 30,
  "media_types": [{"name": "1", "count": 20}, ...]
}
```

## 前端自适应渲染逻辑

前端 `buildReportHTML()` 根据字段存在性动态渲染章节：
- `r.sub_modules` → 显示「子模块负载分布」（默认展开）
- `r.commands || r.sip_methods || r.event_detail` → 显示「操作统计」表（标题自适应默认展开，SIP方法带占比列）
- `r.set_target_count !== undefined` → 显示「设控/停控」
- `r.ne_faults` → 显示「网元通信故障」（默认展开，红色）
- 概览标签栏动态显示：`r.call_id_count`、`r.correlation_id_count`、`r.rtp_session_count`、`r.ligcdr_count`、`r.analysis_time`
- 样本显示：先检查命名样本，无则显示通用 sample_1/2/3（默认展开）
- **🔍 关键发现**：自动生成观察结论（活跃LIID占比、高401拒绝率、心跳失败检测等），每类报告自适应

## 左栏摘要分组逻辑

`buildParsedSummary()` 将 parsed 数据按 command 字段分组：
1. 故障组（link_check/link_error/ne_no_response）→ 红色显示，置顶
2. 设控组（set_target/del_target）→ 青色显示
3. 其他操作组

每个命令卡片显示：次数、LIID列表、NE列表、前3条body样本(200字符截断)

## 导出报告 (仅 Markdown)

```javascript
function exportReport() {
  // 构建 Markdown 字符串，包含全部章节
  downloadFile(md, 'ztlig1-analysis-report.md', 'text/markdown');
}
```

注意：
- `samplesList` 在函数级别定义（不在 if 块内），避免作用域 bug
- `samplesList` 解析逻辑：先检查 ZTLIG1 命名样本（kafka_msg/add_success 等），无则用通用样本 key

## 大文件判断

后端 `app_linux_v4.py`:
```python
is_large = len(content) > 5 * 1024 * 1024
if is_large:
    result["parsed"] = parsed[:5000]   # 用于左栏摘要
    result["raw"] = raw_lines[:1000]   # 右栏仅预览
```

前端:
```javascript
var blob = file.size > 10 * 1024 * 1024 ? file.slice(0, 10 * 1024 * 1024) : file;
var reader = new FileReader();
reader.onload = function(e) { ... };
reader.readAsText(blob, 'utf-8');
```

分析时间: 后端 `time.time()` 计时, 返回值 `analysis_time`, 前端统计卡显示「分析耗时」。
大于5MB的文件在统计卡显示「⚠️大文件」标签。

## 常见前端陷阱

1. `blob.text()` 不是所有浏览器支持 → 用 `FileReader.readAsText()` 替代
2. `.catch()` 中调用未定义函数（如 `analyzeComplete()`）→ ReferenceError 静默吞掉 alert
3. 左栏摘要模式 vs 逐行模式：有 report 时强制摘要模式，无 report 时保持逐行模式
4. 大文件加载提示：必须立即显示（`reader.onload` 前），否则用户以为按钮无反映
5. **`el.querySelector('.card')` 陷阱**：`showLoading()` 中**不能**使用 `el.querySelector('.card')` 查找子元素。`#emptyState` div 没有 `.card` 子元素（只有主内容区有 `.card`），返回 `null` → `.innerHTML` 抛 TypeError → 整个 `analyzeFile()` 函数中断 → 按钮无反应。必须直接用 `el.innerHTML = ...` 替换整个 emptyState。

## 按钮状态反馈

```javascript
function analyzeFile() {
    const btn = document.querySelector('.btn-primary');
    btn.disabled = true;
    btn.textContent = '⏳ 分析中...';
    // ...文件读取中...
    reader.onload = function(e) {
        btn.textContent = '📤 上传分析中...';
        // ...fetch...
        .then(data => {
            btn.disabled = false;
            btn.textContent = '▶ 分析';
            displayResults(data);
        })
    };
    reader.readAsText(blob, 'utf-8');
}
```

按钮状态流转：`▶ 分析 → ⏳ 分析中... → 📤 上传分析中... → ▶ 分析`

## 进度步骤 DOM

`showLoading()` 生成的分步进度 HTML：

```html
<div id="progressSteps" style="text-align:left;font-size:10px;">
  <div id="step0">⏳ 📂 文件读取中... (10MB/22MB)</div>
  <div id="step1">⏳ 📤 已读取 10MB，上传分析中...</div>
  <div id="step2">⏳ 🔄 后端全量处理中 (125K+ 行)</div>
  <div id="step3">⏳ 📊 生成报告...</div>
</div>
```

大文件(>10MB)显示4步，小文件(≤10MB)显示3步。第0步在 setTimeout(100ms) 后自动标记 ✅。

## 关键发现逻辑

```javascript
const findings = [];
if (r.top_liids && r.top_liids.length) {           // 活跃LIID占比
    findings.push('LIID XXXX 出现 N 次 (X.X%)，最为活跃');
}
if (r.sip_methods && r.sip_methods.length) {        // SIP异常检测
    if (sm.name === '401' && sm.count > 100)         // 高401拒绝率
    if (sm.name === 'INVITE' && sm.count > 100)      // 呼叫量活跃
}
if (r.errors > 0) findings.push('共 N 个 ERROR，需关注异常');
if (sample includes 'heart_alive')                   // 心跳失败检测
    findings.push('SSF 心跳发送失败，检查 ZTLIG2 网关连通性');
```
