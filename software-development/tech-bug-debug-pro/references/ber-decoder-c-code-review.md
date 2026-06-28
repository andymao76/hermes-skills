# BER 解码器 C 代码审查 — 模式对比法实战

## 场景

审查中新赛克（Sinovatio）CallCdrAnalyze.c 中华为话单 BER 解码器代码，目标是找出所有调用 `BERDecodeOctetStr` 的函数是否都正确检查了返回值。

## 对比分析

### 三个调用 BERDecodeOctetStr 的 BCD 解码函数

| 函数 | BERDecodeOctetStr 后检查返回值？ | 状态 |
|------|------|------|
| ISDNAddr_Decode | `if(DecodeOK_M != result)` | ✅ 正确 |
| IMSI_Decode | `if(DecodeOK_M != result)` | ✅ 正确 |
| IMEI_Decode | **缺检查** | ❌ Bug |

### IMEI_Decode 的原始代码

```c
UINT8 IMEI_Decode(UINT8 **begin, UINT8 *end, UINT8 *pOctetBuff,
                   UINT16 *actlen, UINT16 MinLen, UINT16 MaxLen)
{
    INT32 result = DecodeOK_M;
    UINT8 num[MAX_IMEI_SIZE] = {0};
    UINT16 size = 0;

    // ... 参数检查 ...

    result = BERDecodeOctetStr(begin, end, num, &size, MAX_IMEI_SIZE, MAX_IMEI_SIZE);
    // ← 无返回值检查！如果 BER 解码失败，num 是垃圾数据

    if(size < MinLen || size > MaxLen)  // 长度检查，但数据已经无效
        return FALSE;

    // BCD 转换——当 BER 解码失败时这里输出垃圾
    for(i=0; i<size; i++)
        pOctetBuff[i] = ((num[i]<<4)&0xF0) + ((num[i]>>4)&0x0F);
```

### 修复

在第462行 BERDecodeOctetStr 调用后添加：

```c
if( DecodeOK_M != result )
{
    // 记录日志并返回错误
    return FALSE;
}
```

## 模式对比法的通用步骤

1. **确定底层 API** — 找出代码库中被多次调用的同一个函数（如 BERDecodeOctetStr、fread、malloc）
2. **收集所有调用点** — 用 grep/search 列出所有调用该 API 的位置
3. **对比错误处理** — 逐一检查每个调用点后的错误处理代码
4. **识别遗漏** — 缺少检查的调用点即是 Bug
5. **修复** — 参照其他函数的处理模式补充缺失的检查

## 适用场景

- BER/TLV 协议栈解码代码
- 文件 I/O 操作（fread/fwrite → 检查返回值）
- 内存操作（malloc/realloc → 检查 NULL）
- 网络通信（send/recv → 检查实际收发字节数）
