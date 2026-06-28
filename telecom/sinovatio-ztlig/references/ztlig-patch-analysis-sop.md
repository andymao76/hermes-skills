# ZTLIG 补丁二进制分析 SOP

> 分析目标：对 ZTLIG 系统各模块的补丁二进制进行逆向分析
> 核心原则：**agc(调用图) > pdc(伪C) > afl|wc -l(函数计数)**
> 安全约束：ZTLIG/Sinovatio 涉密二进制禁止上传外网 LLM

## 工具链

| 工具 | 用途 | 分析深度 |
|:----:|------|:--------:|
| `file` | 识别 ELF 架构/类型 | 表面 |
| `readelf` | 提取 BuildID | 表面 |
| `strings` | 提取可读文本 | 中等 |
| `md5sum` | 文件指纹 | 表面 |
| `diff` | 跨版本对比 | 表面 |
| `r2` (radare2) | **调用图/控制流图/伪C** | **深度** |

## 6 步分析法

### Step 1: 目录摸底
```bash
ls -la /path/to/patches/
for d in */; do echo "=== $d ===" && ls -la "$d"; done
```

### Step 2: 二进制识别
```bash
file <每个二进制>
```
关键提取: ARM aarch64 vs x86-64 / executable vs .so / BuildID / not stripped

### Step 3: BuildID 追踪
```bash
readelf -n <文件> | grep BuildID
md5sum <文件>
```
建立版本演进表（大小 + BuildID + MD5）

### Step 4: strings 功能分析
```bash
strings <文件> | grep -iE "error|fail|alloc|version|init" | sort -u | head -30
strings <文件> | grep -E "^/home/" | sort -u   # 源码路径→判断开发者
```

### Step 5: r2 程序流分析（核心）

```bash
# 层级1-2: 函数计数+搜索（最低价值）
r2 -e bin.cache=true -q -c "aaa; afl|wc -l" <文件>
r2 -e bin.cache=true -q -c "aaa; afl~cJSON" <文件>

# 层级3: 函数体积追踪（暴涨=功能增强）
r2 -e bin.cache=true -q -c "aaa; afl~decode_kafka_addmsg" <文件>

# 层级4: 调用图（最高价值）
r2 -e bin.cache=true -q -c "aaa; s dbg.HI3PushMsgToOwls; agc" <文件>

# 层级5: 控制流图
r2 -e bin.cache=true -q -c "aaa; s dbg.HI3PushMsgToOwls; agf" <文件>

# 层级6: 伪C反编译
r2 -e bin.cache=true -q -c "aaa; s dbg.HI3PushMsgToOwls; pdc" <文件>

# 层级7: 交叉引用
r2 -e bin.cache=true -q -c "aaa; / UsrIP; axt" <文件>
```

### Step 6: 跨版本对比
```bash
diff <(strings old.so | sort) <(strings new.so | sort) | head -30
ls -la old.so new.so
```

## 实战案例

### libhi3pro.so usrip 修复
**表象**: "23口关联消息修改usrip为点分十进制"
**strings**: acUsrIp 字段从无到有
**agc调用图**:
```
11-14: memset → inet_ntop → KafkaProduceMsgByKey
12-10: memset → cJSON_CreateObject → cJSON_CreateString("UsrIP") → 
        cJSON_AddItemToObject → cJSON_PrintUnformatted → KafkaProduce → cJSON_Delete
```
**结论**: 不是简单改字段编码，是整个消息格式从二进制TLV重构为JSON

### libwebhi1.so 10-19 重构
- `decode_kafka_addmsg`: 260B → 2,240B (8.6倍) — 加入9字段校验
- `decode_kafka_modmsg`: 新增 2,140B — 修改消息解码
- Redis 函数: 11 → 16 — 新增仲裁/删除/同步

## 三级联动分析
- 协议层: ETSI-ASN1-Assistant 解码 HI2/X2 PCAP
- 代码层: r2(agc/agf/pdc) 反编译 decoder .so
- 系统层: 完整 tmp_so/ (121个) 交叉引用
