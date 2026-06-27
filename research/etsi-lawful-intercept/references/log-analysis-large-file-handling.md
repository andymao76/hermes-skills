# 日志分析工具大文件处理

## 问题: Chrome SIGILL 崩溃

当通过浏览器上传数百 MB 的日志文件（如 ztlig1.300.txt 521MB）时，Chrome 的 `FileReader.readAsText()` 将整个文件读入 V8 堆内存，超出限制后操作系统发送 SIGILL 终止进程。

## 解决方案: 前后端双重截断

### 前端 (x_interface.html)
```javascript
const MAX_BYTES = 5 * 1024 * 1024;  // 5MB
const blob = file.size > MAX_BYTES ? file.slice(0, MAX_BYTES) : file;
reader.readAsText(blob);
```
- 选文件时显示大小: `(521.0MB) ⚠仅分析前5MB`
- 超 5MB 弹窗确认

### 后端 (app_linux_v4.py)
```python
MAX_CONTENT = 5 * 1024 * 1024
if len(content) > MAX_CONTENT:
    content = content[:MAX_CONTENT]
```

## 适用场景
- SSF (SIP 信令日志)
- RVF (RTP 媒体日志)
- ZTLIG1 (X1 管理日志, 可超 500MB)
- ZTLIG2 (X2 IRI 日志)

## 最佳实践
1. 生产日志可能数 GB，Web 工具必须做文件大小限制
2. 前端和后端双重截断：前端防浏览器 OOM，后端防护服务端
3. 文件选择时即显示大小和截断提示
4. 大文件建议分段分析（按时间范围切割或写本地脚本）
