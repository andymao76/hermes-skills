# Bug③ 修复：IMEI_Decode 缺少 BER 解码结果检查

## 文件
`CallCdrAnalyze.c` — `IMEI_Decode()` 函数

## 问题
第462行调用 `BERDecodeOctetStr()` 后未检查返回值。对比 `IMSI_Decode()` 和 `ISDNAddr_Decode()` 都有正确检查，`IMEI_Decode` 遗漏。

## 修复
```diff
     result = BERDecodeOctetStr(begin, end, num, &size, MAX_IMEI_SIZE, MAX_IMEI_SIZE);
+    if (DecodeOK_M != result) {
+        WZXINLOG "%s [IMEI_Decode]decode IMEI BER failed!\n", ERROR_LEVEL);
+        return FALSE;
+    }
```

## 影响
BER 解码失败时，函数仍使用未初始化的 `num[]` 进行 BCD 转换，输出垃圾 IMEI。

## 验证
确认 `IMSI_Decode` 的相同位置有正确的检查代码。
