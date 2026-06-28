# BER 解码器 Bug 模式参考

来源：`CallCdrAnalyze.c`（中新赛克华为话单解码器）

## 已发现的 Bug 类型

### B1. memset 只清二维数组第一维

```c
static UINT8 g_cdr_read_buf[MAX_CDR_OPERATION_NUM][MAX_CDR_FILEBUF_LEN];
memset(g_cdr_read_buf, 0x00, MAX_CDR_FILEBUF_LEN);  // ❌ 只清第0行
memset(g_cdr_read_buf, 0x00, sizeof(g_cdr_read_buf)); // ✓ 全清
```

### B2. snprintf + memcpy 参数混乱

```c
snprintf(tmp_s, num_size, "%02x", num[i]);
memcpy(ptr, tmp_s, num_size);  // ❌ 拷贝 num_size 字节，但 snprintf 只写了2~3字节
// strcat 继续拼接垃圾数据
```

### B3. BER 解码后未检查返回值

```c
result = BERDecodeOctetStr(begin, end, num, &size, MAX, MAX);
// ← 缺少 result 检查，后续用未初始化的 num
if(size < MinLen || size > MaxLen) { ... }  // 跳过后继续使用 num
```

### B4. fread 不足读取未处理

```c
UINT32 blen = fread(buf, 1, expected_len, fd);
if(!blen) { ... }  // ❌ blen < expected_len 但 > 0 时通过检查
// 拿着不完整的 buf 继续解码
```

### B5. for 循环条件写反

```c
for(i=0; i++; i < MAX)  // ❌ i++ 在条件位，循环体一次都不执行
for(i=0; i < MAX; i++)  // ✓ 正确写法
```

### B6. memset 用了 sizeof(指针)

```c
memset(&cdrComm->cdr_info, 0x00, sizeof(CALL_Cdr_Info_T*));  // ❌ 只清4/8字节
memset(&cdrComm->cdr_info, 0x00, sizeof(CALL_Cdr_Info_T));   // ✓ 清整个结构体
```

### B7. 空指针检查误检为双指针

```c
if(!begin)  // ❌ begin 是 UINT8**，函数开头已检查 != NULL
if(!(*begin))  // ✓ 检查的是返回值
```

## 排查清单

对照以下模式检查代码：

- [ ] memset 的 size 参数是否等于预期的对象大小？
- [ ] 所有 BER Decode 函数（BERDecodeInt / BERDecodeOctetStr / BERDecodeEnumBYTE）的返回值是否都被检查？
- [ ] fread 返回值和期望值比较是否完整？
- [ ] for 循环的三个表达式写法是否正确？
- [ ] 指针类型和取值操作是否匹配？
- [ ] 二维数组操作时是否用了 `sizeof(array)` 而不是单个维度？
- [ ] 函数参数类型是否和调用处的值匹配？
