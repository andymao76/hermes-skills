# BER 解码器 C 代码审查指南

## 背景

在审查（中兴/中新赛克）BER 编解码器的 C 源码时，发现多类重复性 Bug。本文档归纳这些模式，供后续代码审查使用。

## 模式一：BERDecodeOctetStr 返回值未检查

### 正确做法（如 ISDNAddr_Decode / IMSI_Decode）

```c
result = BERDecodeOctetStr( begin,end,num,&size,MinLen,MaxLen );
if( DecodeOK_M != result )
{
    WZXINLOG "%s [FuncName]decode failed!\n", ERROR_LEVEL);
    return FALSE;
}
```

### 错误做法（如 IMEI_Decode 原始版本）

```c
result = BERDecodeOctetStr( begin,end,num,&size,MAX_IMEI_SIZE,MAX_IMEI_SIZE);
// ← 缺少 result 检查！BER 解码失败时 num 为垃圾数据
if(size < MinLen || size > MaxLen)
{
    // 尺寸检查通过了，但 num 内容不可用
    ...
}
```

**后果**：BER 解码失败（如码流损坏、长度越界）后继续执行 BCD 转换，输出含垃圾数据的 IMEI 结果。

**修复补丁**：
```c
// 在 result = BERDecodeOctetStr(...) 之后添加：
if( DecodeOK_M != result )
{
    WZXINLOG "%s [IMEI_Decode]decode IMEI BER failed!\n", ERROR_LEVEL);
    return FALSE;
}
```
对比同文件中的 `IMSI_Decode` 和 `ISDNAddr_Decode`，两者都有此检查，`IMEI_Decode` 是复制模板时遗漏。

### 排查清单

审查 BER 解码函数时，检查以下每个 `BERDecode*` 调用是否有返回值检查：

| 函数 | 应检查返回值 | 常见遗漏点 |
|------|------------|-----------|
| `BERDecodeOctetStr` | ✅ 必须检查 | IMEI_Decode 曾遗漏 |
| `BERDecodeInt` | ✅ 必须检查 | 较少遗漏 |
| `BERDecodeIdentifier` | ✅ 必须检查 | 较少遗漏 |
| `BERDecodeLength` | ✅ 必须检查 | 较少遗漏 |
| `BERGetcharMovPtr` | ✅ 必须检查 | 内部函数，错误会冒泡 |

## 模式二：memset 清零只清指针而非结构体

```c
// ❌ 错误
memset(&cdrComm->cdr_info, 0x00, sizeof(CALL_Cdr_Info_T*));
// sizeof(指针) = 4 或 8，只清了指针大小

// ✅ 正确
memset(&cdrComm->cdr_info, 0x00, sizeof(CALL_Cdr_Info_T));
// 或
memset(&cdrComm->cdr_info, 0x00, sizeof(cdrComm->cdr_info));
```

特别在 switch-case 分支中（多个 record type 时最容易出现）。

## 模式三：for 循环条件写反

```c
// ❌ 错误 — 循环体永不执行
for(i=0; i++; i < MAX)

// ✅ 正确
for(i=0; i < MAX; i++)
```

这类 Bug 在静态代码检查（如 KW、Coverity）中应该能检出，但如果项目未启用静态检查则会在运行时暴露。

## 模式四：空指针检查检查了错误的变量

```c
// ❌ 错误 — begin 是 UINT8 **，已在函数开头检查过不为 NULL
if(!begin)  // 永远为 false

// ✅ 正确 — 检查返回值
if(!(*begin))
```

## 模式五：sizeof 在指针和数组的误用

| 声明 | sizeof 含义 | 正确写法 |
|------|------------|---------|
| `UINT8 buf[64]` | `sizeof(buf) = 64` | 直接用 `sizeof(buf)` |
| `UINT8 buf[MAX][N]` | `sizeof(buf) = MAX*N` | 整数组: `sizeof(buf)`；单行: `sizeof(buf[0])` |
| `char *p` | `sizeof(p) = 4 或 8` | 需显式传入或检查缓冲区长度 |

**典型错误**：二维数组 `g_cdr_read_buf[MAX][N]` 用 `memset(buf, 0, N)` 而不是 `memset(buf, 0, sizeof(buf))`——结果只清了第一行。

## 模式六：fread 返回值处理

```c
// ❌ 错误 — 只检查 !blen（完全读取失败）
blen = fread(buf, 1, expected, fcdr);
if(!blen) { /* error */ }
// 当 blen < expected 但 > 0 时（文件尾），拿着不完整数据继续解码

// ✅ 正确
blen = fread(buf, 1, expected, fcdr);
if(blen < expected)
{
    if(feof(fcdr)) { /* 读到文件尾 */ }
    else { /* 读取错误 */ }
}
```

## 外部对比：ztlig_ber.c 的质量

原始 `ztlig_ber.c`（王晶晶，2011年）的 BER 底层库质量较高：
- 每个函数的开头都有 `if(NULL == begin || *begin == NULL || end == NULL)` 空指针检查
- 每步 `BERGetcharMovPtr` 调用后都有结果检查
- 返回值路径完整，无遗漏

上层 `CallCdrAnalyze.c`（hf，2018年）的 Bug 多源于：
- 复制粘贴 `IMSI_Decode` 模版创建 `IMEI_Decode` 时遗漏了检查
- switch-case 多分支场景下的 `memset` 尺寸误用
- 对 `fread` 返回值期望过于乐观

## 模式七：Hex 字符串转换中的缓冲区操作错误

```c
// ❌ 错误 — snprintf 写入 2~3 字节，memcpy 拷贝 num_size 字节
void ArrayToString(char *ptr, uint8_t *num, int num_size)
{
    char tmp_s[12];
    for (i = 0; i < num_size; i++) {
        bzero(tmp_s, num_size);          // num_size 可能 > 12 → 越界
        snprintf(tmp_s, num_size, "%02x", num[i]);  // 实际写 3 字节
        if (1 == flag) {
            memcpy(ptr, tmp_s, num_size);  // 拷贝 num_size 字节，含垃圾
            flag = 0;
        } else {
            strcat(ptr, tmp_s);           // 越拼越乱
        }
    }
}

// ✅ 正确 — 逐字节写入
void ArrayToString(char *ptr, uint8_t *num, int num_size)
{
    for (int i = 0; i < num_size; i++) {
        sprintf(ptr + i * 2, "%02x", num[i]);
    }
}
```

**排查要点**：
- 检查所有 `snprintf` + `memcpy` 组合，确认拷贝长度与写入长度一致
- `bzero` 的大小不能超过局部数组大小（本例中 `tmp_s[12]` 但 `bzero(tmp_s, num_size)` 中的 `num_size` 可达 9，险过）
- 优先使用一次 `sprintf` 写入正确偏移，避免多段 `strcat` 拼接

## 模式八：函数返回类型与检查值不匹配

```c
// ❌ 问题 — IMEI_Decode 声明返回 UINT8 (0=FALSE, 1=TRUE)
// 但调用方用 INT32 result 接收并检查 TRUE 宏
UINT8 IMEI_Decode(...);
INT32 result = IMEI_Decode(...);   // UINT8 → INT32 隐式转换
if(TRUE == result) { ... }         // TRUE 宏定义不确定，可能 ≠ 1

// ✅ 更安全 — 保持返回类型与检查方式一致
// 方式A：统一用 INT32 + DecodeOK_M 风格
INT32 IMEI_Decode(...) {
    return DecodeOK_M;  // = 0
    return DecodeError_M;  // = 非0
}
result = IMEI_Decode(...);
if(DecodeOK_M == result) { ... }

// 方式B：统一用 UINT8 + TRUE/FALSE 风格
UINT8 IMEI_Decode(...) {
    return TRUE;   // = 1
    return FALSE;  // = 0
}
if(TRUE == IMEI_Decode(...)) { ... }
```
