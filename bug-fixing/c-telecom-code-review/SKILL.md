---
name: c-telecom-code-review
description: C 代码审查模式集，聚焦电信/合法监听系统的 C 源码分析、Bug 模式识别和修复验证
triggers:
  - C 代码审查 / code review C
  - BER 编解码代码分析
  - 华为/中兴话单解析代码审计
  - 遗留 C 代码 Bug 排查
---

# C 代码审查 — 电信/LI 系统模式集

## 适用场景

审查或修复电信领域的 C 源码，特别是 BER/TLV/ASN.1 编解码相关代码、合法监听系统话单解析、存在多版本维护痕迹的遗留 C 代码。

## 通用检查清单

### 1. BER 解码结果检查（高频 Bug）

**症状**：调用 BER 解码函数后未检查返回值，解码失败时仍使用未初始化缓冲区。

**检查点**：
- `BERDecodeOctetStr`、`BERDecodeIdentifier`、`BERDecodeLength`、`BERDecodeInt` 等函数返回 `INT32`，需与 `DecodeOK_M` 比较
- 常见遗漏模式：
  ```c
  result = BERDecodeOctetStr(...);
  // ← 缺少 result 检查
  if (size < MinLen || size > MaxLen) { ... }
  ```
- **正确模式**：
  ```c
  result = BERDecodeOctetStr(begin, end, buf, &size, min, max);
  if (DecodeOK_M != result) {
      LOG_ERROR("[Func]BER decode failed!");
      return FALSE;
  }
  ```

**参考实现**（已有正确检查的样板）：`ISDNAddr_Decode`、`IMSI_Decode` 正确；`IMEI_Decode` 已修复（曾遗漏）。

### 2. memset 清零指针 vs 结构体

```c
memset(&info, 0x00, sizeof(Type_T*));  // ❌ 只清了指针大小
memset(&info, 0x00, sizeof(Type_T));   // ✅ 正确
```
**检查点**：switch 分支中多个 memset 调用，易复制粘贴导致参数未改。

### 3. memset 二维数组只清第一维

```c
static UINT8 buf[MAX_ROWS][MAX_COLS];
memset(buf, 0, MAX_COLS);    // ❌ 只清了第一行
memset(buf, 0, sizeof(buf)); // ✅ 全部清零
```

### 4. for 循环条件写反

```c
for (i = 0; i++; i < MAX)  // ❌ 永不执行
for (i = 0; i < MAX; i++)  // ✅
```

### 5. fread 返回值处理

```c
blen = fread(buf, 1, size, fp);
if (!blen) { ... }            // ❌ 没处理部分读取
if (blen < size) { ... }      // ✅
```

## 修复验证流程

1. 确认根因（参照 `bug-fixing-openclaw` 的 triage 流程）
2. 对比同类函数的正确实现
3. 应用修复
4. 更新知识库：`li/<vendor>/` 或 `program-info/c-language/`
5. 变更日志记录修正了哪个函数和什么模式
