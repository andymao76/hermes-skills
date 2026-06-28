---
name: tech-bug-debug-pro
description: 七步调试协议 + 语言特定调试命令 (Python/Node.js/Swift/CSS/网络/Git Bisect)。覆盖 pdb、inspect、lldb、curl、dig、lsof 等工具。搭配 log-analyzer + systematic-debugging + bug-fixing 形成完整排查工作流。
tags: [调试, 七步协议, pdb, lldb, git-bisect, 根因分析]
---

# Debug Pro — 七步调试协议

## 七步调试协议

| 步骤 | 操作 | 产出 |
|------|------|------|
| **1. 复现** | 稳定复现 Bug，记录环境、输入、步骤 | 稳定复现路径 |
| **2. 隔离** | 缩小范围：二分法注释代码、git bisect 找引入 commit | 可疑范围 |
| **3. 假设** | 提出可验证的根因理论 | 明确假设 |
| **4. 检测** | 加日志、断点、断言 | 证据数据 |
| **5. 验证** | 确认根因。假设错误则回第3步 | 根因确认 |
| **6. 修复** | 最小化修复，禁止边调试边重构 | 修复方案 |
| **7. 回归** | 写测试用例捕获此 Bug，验证通过 | 回归测试 |

## 语言特定调试

### JavaScript / TypeScript

```bash
# Node.js 调试器
node --inspect-brk app.js
# Chrome DevTools → chrome://inspect

# 控制台调试
console.log(JSON.stringify(obj, null, 2))
console.trace('Call stack here')
console.time('perf'); /* code */ console.timeEnd('perf')

# 内存泄漏
node --expose-gc --max-old-space-size=4096 app.js
```

#### 🚨 HTML 模板内嵌 JS：花括号不匹配导致整个脚本块静默不加载

**症状**: 点击按钮无反应，Flask/后端未收到请求，浏览器 F12 控制台无任何 JS 报错。
HTML 页面正常渲染，`<script>` 标签存在，但 `onclick` 调用的函数不存在。

**根因**: `<script>` 标签内的 JS 存在语法错误（最常见：多余的 `}` 使 `{`/`}` 不匹配）。
浏览器解析脚本失败后**丢弃整个脚本块**（而非仅跳过错误行），导致所有函数均未定义。
这是浏览器的安全设计 — 脚本要么完整执行，要么完全不执行。

**现象**:
- `{`/`}` 数量不相等（如 116 开 / 117 闭）
- `analyzeFile`、`displayResults` 等函数在 `typeof` 下为 `undefined`
- Flask 日志无收到 API 请求（因为请求从未被发出）

**排查流程**:
1. 在浏览器 F12 Console 中执行 `typeof analyzeFile` — 返回 `'undefined'` 而非 `'function'`
2. 确认脚本语法错误：用 Python 或 Node.js 校验花括号平衡
```bash
# Python 快速检查
python3 -c "
import re
s = open('template.html').read()
scripts = re.findall(r'<script[^>]*>(.*?)</script>', s, re.DOTALL)
for i, script in enumerate(scripts):
    print(f'Script #{i}: {script.count(\"{\")}/{\"\"}{script.count(\"}\")}')
"
```
3. 逐字符扫描确认具体在哪行多出括号
4. 删除多余的括号后刷新页面（需 Ctrl+F5 强制清理缓存）
5. 验证：`typeof analyzeFile` → `'function'`

**根因排查注意事项**:
- 删除 `if/else/for/function` 结构时，各分支的 `{ }` 需一并清理
- 复制/粘贴代码时容易产生多余括号，修改后应验证平衡
- 对于 500+ 行单文件 JS，定期做括号匹配校验是廉价有效的预防手段

#### 🚨 Blob.text() vs FileReader.readAsText() 兼容性

**症状**: 使用 `file.text().then(...)` 读取大文件时页面卡死或某些浏览器不工作。

**根因**: `Blob.text()` 是 ES2021 API，在老旧浏览器中不支持。且 `.text()` 返回 Promise，
在非常大的文件（>10MB）上浏览器实现可能有差异。

**修复**: 使用 `FileReader.readAsText()` 作为替代，兼容性更好（IE10+，所有现代浏览器均支持）。

```javascript
// 推荐: 兼容性好
var blob = file.size > MAX ? file.slice(0, MAX) : file;
const reader = new FileReader();
reader.onload = function(e) {
    var text = e.target.result;
    // ... 处理 text
};
reader.readAsText(blob, 'utf-8');

// 不推荐: Blob.text() 在老旧浏览器不支持
file.text().then(text => { ... });
```

### Python

```bash
# 内置调试器
python -m pdb script.py

# 代码中设断点
breakpoint()  # Python 3.7+

# 详细跟踪
python -X tracemalloc script.py

# 性能分析
python -m cProfile -s cumulative script.py
```

#### 🚨 Flask 静态文件 404：`static_folder` 路径与模块目录的关系

**症状**: Flask 返回 `404`，访问 `/static/css/style.css` 文件明明存在却 404。

**根因**: `Flask(__name__)` 的 `static_folder` 默认解析为模块文件所在目录的 `static/` 子目录。当 `app.py` 在 `src/` 下时，Flask 找的是 `src/static/`，而非项目根目录的 `static/`。

**修复**:
```python
# app.py 在 src/ 下，static/ 在项目根目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, static_folder=os.path.join(BASE_DIR, '..', 'static'), static_url_path='/static')
```

**排查**:
```python
# 检查 Flask 实际使用的 static 路径
print(app.static_folder)  # 输出当前解析到的路径
# 如果路径是 src/static 而不是 project_root/static → 需要修正
```

**预防**: 创建 Flask 项目时始终注意 `app.py` 文件位置与 `static/` 目录的层级关系，显式设置 `static_folder`。

#### 🚨 Python 导入副作用陷阱：包级别的 `__getitem__` 拦截

**症状**: 调用 `data[offset + header_len:]`（普通 bytes 切片）却抛出 `KeyError: slice(14, None, None)`，堆栈指向某个依赖包的 `__getitem__` 而非正常切片逻辑。

**根因**: 某些包（典型如 `dpkt`）的 `Packet` 基类定义了 `__getitem__(self, k)`，当传参不是 `str` 时直接 `raise KeyError(k)`。如果某个变量被赋值为该包的对象而非 bytes，切片语法 `obj[start:stop]` 会触发 `__getitem__` 而非 Python 原生切片。

**排查流程**:
1. 定位到具体哪个变量触发了 KeyError（堆栈中的 data[14:] 行）
2. type(data) 确认变量类型 — 不是 bytes 而是 dpkt.Packet 或其他
3. 回查赋值路径：这个变量原本应该是 bytes，从哪里来的
4. 如果问题出现在函数的 data 形参 → 检查调用方传了什么
5. 修复：确保变量类型正确（显式 type 转换或在源头修正）

**典型场景**: 在 `pre_decode_split_report(data, header_len)` 中 `data` 参数期望 bytes，但调用方传入了 dpkt 解析后的 Packet 对象。当函数执行 `data[offset + header_len:]` 时触发 dpkt 的 `__getitem__` 而非 bytes 切片。

**预防**:
- 函数形参尽量声明类型注解 `data: bytes`，在入口处加 `assert isinstance(data, bytes)`
- 导入 dpkt 的模块中，避免使用 `data` 作为变量名（与 dpkt.Packet 的 data 属性产生误导）
- 对依赖包的关键方法签名要敏感：`dpkt.Packet.__getitem__` 只接受 str key，不接受 slice

### C / Embedded

#### 🚨 memset 清零：sizeof(指针) 而非 sizeof(结构体)

**症状**: 调用 memset 清零结构体后，部分字段仍是垃圾值。

**根因**: `memset(&cdrComm->cdr_info, 0, sizeof(CALL_Cdr_Info_T*))` — `sizeof(指针)` 在 64 位系统上只有 8 字节，而结构体可能远超此值。绝大多数成员未被清零。

**排查**: 检查 memset 调用的第三个参数，确认是 `sizeof(结构体)` 而非 `sizeof(指针)`。

```c
// ❌ 错误：只清 8 字节
memset(&info, 0, sizeof(StructType*));

// ✅ 正确：清整个结构体
memset(&info, 0, sizeof(StructType));
// 或
memset(&info, 0, sizeof(info));
```

#### 🚨 for 循环条件顺序错误：循环体一次都不执行

**症状**: 某段循环逻辑的行为像完全没执行过，初始化/遍历结果为空。

**根因**: `for(i=0; i++; i < MAX)` — 循环条件中的 `i++` 在第一次判断时值为 0（false），循环体被完全跳过。

**排查**: 检查 `for` 的第二部分（条件表达式），如果条件写成了递增表达式，循环永远不会执行。

```c
// ❌ 错误：i++ 在首次判断时为 0 (false)，循环体永不执行
for(i=0; i++; i < MAX) { ... }

// ✅ 正确：i < MAX 才是条件
for(i=0; i < MAX; i++) { ... }
```

#### 🚨 fread 不足读取未处理

**症状**: 文件未读完，读到不完整的结构体或 BER TLV 数据，解码出错。

**根因**: 只检查 `if(!blen)`（完全失败），忽略了 `0 < blen < expected_len` 的部分读取情况。拿着不完整的缓冲区继续解码，导致越界或错误解码。

```c
// ❌ 错误：只检查完全失败
UINT32 blen = fread(buf, 1, expected_len, fp);
if(!blen) { /* 报错 */ }
// ← blen < expected_len 但 > 0 时悄无声息地传入不完整的 buf

// ✅ 正确：检查是否读到足够长度
size_t blen = fread(buf, 1, expected_len, fp);
if(blen < expected_len) {
    // 处理不足读取（文件尾/EIO/信号中断）
}
```

**备注**: `fread` 返回 `size_t`（64 位系统 8 字节），赋值给 UINT32 会被隐式截断。建议用 `size_t` 声明。

#### 🚨 十六进制字符串拼接：snprintf + memcpy 参数错乱

**症状**: 数组转十六进制字符串时得到乱码或部分丢失。

**根因**: 常见错误是用 `snprintf` 格式化一个字节后，用 `memcpy` 按 `num_size`（原始数组长度）而非实际写入长度拷贝。第二次 `strcat` 时源数据格式已损坏。

```c
// ❌ 错误：memcpy 拷贝 num_size 字节，但 snprintf 只写了 3 字节
char tmp_s[12];
for(i=0; i<num_size; i++) {
    snprintf(tmp_s, num_size, "%02x", num[i]);
    memcpy(ptr, tmp_s, num_size);  // ← 拷贝了垃圾数据
    strcat(ptr, tmp_s);            // ← 越读越乱
}

// ✅ 正确：直接计算偏移
void bytes_to_hex(char *ptr, uint8_t *num, int num_size) {
    for(int i = 0; i < num_size; i++)
        sprintf(ptr + i * 2, "%02x", num[i]);
}
```

#### 🚨 双指针参数的空指针检查误检

**症状**: 空指针检查未生效，实际为 NULL 的指针被传入后续解码函数。

**根因**: `begin` 是 `UINT8 **` 类型，`if(!begin)` 检查的是双指针参数本身（函数入口已被上一级确保非 NULL），而非其指向的内容（`*begin`）。

```c
// ❌ 错误：检查了双指针本身，不是返回值
if(!begin) { ... }  // begin 是 UINT8**，已经非 NULL

// ✅ 正确：检查解引用后的值
if(!(*begin)) { ... }
```

#### 🚨 二维数组 memset 只清了第一行

**症状**: 多实例场景下，第 1 个实例正常，后续实例数据残留旧值。

**根因**: `UINT8 arr[MAX_OP][MAX_BUF]` 总大小是 `MAX_OP * MAX_BUF`。memset 时只传了 `MAX_BUF` 仅清零第 0 行。

```c
// ❌ 错误：只清了第一维
memset(g_arr, 0, MAX_CDR_FILEBUF_LEN);

// ✅ 正确：清整个数组
memset(g_arr, 0, sizeof(g_arr));

// 或只清当前行（更精准）
memset(g_arr[index], 0, MAX_CDR_FILEBUF_LEN);
```

#### 🚨 参数类型截断：UINT8 无法承载大值

**症状**: 文件/缓冲区长度超过 255 时，传入的读取长度被截断。

**根因**: 将 int 型长度值传给 UINT8 参数时被隐式截断（如 256 → 0）。

```c
// 声明：void func(UINT8 len)
// 调用：func(256);           // → len = 0
// 调用：func(BIG_VALUE);     // 如果 > 255，也被截断
```

**预防**: 文件长度相关参数使用 UINT16/UINT32/size_t，避免 UINT8。

#### 🚨 函数返回值未检查：直接使用可能无效的输出

**症状**: 解码结果出现不可能的值（如不合理的 IMEI/IMSI）。

**根因**: 调用解码函数后不检查返回值，假设输出缓冲区已有效。解码失败时输出缓冲区是垃圾数据。

```c
// ❌ 错误：返回值被忽略
result = IMEI_Decode(begin, end, buf, &size, min, max);
bcd2ascii(buf, out, size, 1);  // ← 上面失败则 buf 是垃圾

// ✅ 正确：先检查再使用
result = IMEI_Decode(begin, end, buf, &size, min, max);
if(result != TRUE) { /* 处理 */ return; }
bcd2ascii(buf, out, size, 1);
```

#### 🔍 模式对比法（Pattern Comparison）：通过函数对比发现遗漏的返回值检查

**适用场景**: 代码库中有多个函数调用相同的底层 API（如 BERDecodeOctetStr、fread、malloc），有些检查了返回值，有些没有。

**技术**: 找到调用同一 API 的所有函数，并排对比它们的错误处理模式。缺失检查的那个就是 Bug。

**例：BER 解码器代码审查**
```c
// 函数 A：ISDNAddr_Decode — ✅ 有检查
result = BERDecodeOctetStr(begin, end, buf, &size, min, max);
if(DecodeOK_M != result) { /* 报错 */ return FALSE; }

// 函数 B：IMSI_Decode — ✅ 有检查
result = BERDecodeOctetStr(begin, end, buf, &size, min, max);
if(DecodeOK_M != result) { /* 报错 */ return FALSE; }

// 函数 C：IMEI_Decode — ❌ 遗漏检查
result = BERDecodeOctetStr(begin, end, buf, &size, min, max);
// ← 无检查！解码失败仍继续使用 buf
if(size < MinLen) { /* 只检查长度，但 buf 已损坏 */ }
```

**排查步骤**:
1. 列出所有调用同一底层 API 的函数
2. 逐一对比每个调用点之后的错误处理
3. 标记缺少检查的调用点
4. 补充缺失的返回值检查

**适用场景**（不仅限于 C）:
- Python: 多个函数调用 `requests.get()` / `open()` / `subprocess.run()`
- JS/TS: 多个函数调用 `fetch()` / `readFile()` / `JSON.parse()`
- Go: 多个函数调用 `ioutil.ReadAll()` / `json.Unmarshal()` / `db.Query()`

**提示**: 对于 BER/TLV 等结构化数据解码，API 调用失败通常意味着**码流损坏或编码错误**，此时必须中断处理而非继续使用输出缓冲区。比较常见的有 `BERDecodeIdentifier`、`BERDecodeLength`、`BERDecodeOctetStr`、`BERGetcharMovPtr` 这四类调用的检查完整性。

### Swift / iOS

```bash
# LLDB
lldb ./MyApp
(lldb) breakpoint set --name main
(lldb) run
(lldb) po myVariable

# Xcode: Product → Profile (Instruments)
```

### CSS / 布局

```css
/* 所有元素轮廓 */
* { outline: 1px solid red !important; }

/* 特定元素调试 */
.debug { background: rgba(255,0,0,0.1) !important; }
```

### 网络

```bash
# HTTP 调试
curl -v https://api.example.com/endpoint
curl -w "@curl-format.txt" -o /dev/null -s https://example.com

# DNS
dig example.com
nslookup example.com

# 端口
lsof -i :3000
netstat -tlnp
```

### Git Bisect（二分查找引入 Bug 的 commit）

```bash
git bisect start
git bisect bad              # 当前有 Bug
git bisect good abc1234     # 已知正常的 commit
# Git 自动 checkout 中间 commit → 测试
git bisect good  # 或 git bisect bad
# 重复直到找到根因 commit
git bisect reset
```

## 常见错误模式

| 错误 | 原因 | 修复 |
|------|------|------|
| Cannot read property of undefined | 缺空值检查或数据结构错误 | 可选链(?.)或数据验证 |
| ENOENT | 文件/目录不存在 | 检查路径，创建目录 |
| CORS error | 后端缺 CORS 头 | 加 CORS 中间件 |
| Module not found | 缺依赖或 import 路径错误 | npm install，检查 tsconfig paths |
| Export named 'X' not found | 模块版本升级后导出名变更 | 检查 dist exports，对比 v1→v2 变更（参考 references/vite-module-export-mismatch.md） |
| Hydration mismatch (React) | 服务端/客户端渲染不一致 | 确保一致渲染，useEffect 处理客户端逻辑 |
| Segmentation fault | 内存损坏/空指针 | 检查数组边界、指针有效性 |
| Connection refused | 服务未在预期端口运行 | 检查服务状态、端口/主机 |
| Permission denied | 文件/网络权限 | 检查 chmod、防火墙、sudo |

## 快速诊断命令

```bash
# 端口占用
lsof -i :PORT

# 进程详情
ps aux | grep PROCESS

# 文件变更监控
fswatch -r ./src

# 磁盘空间
df -h

# 系统资源
top -l 1 | head -10
```
