# LI Flask Web 工具开发参考

ETSI ASN.1 Assistant V3.1 开发过程中沉淀的可复用模式，适用于 LI 协议解码类 Web 工具的构建与调试。

## Flask 子目录部署 — static 404 修复

当 `app.py` 在 `src/` 子目录、`static/` 在项目根目录时：

```python
# 错误（Flask默认找 src/static/）
app = Flask(__name__)

# 正确
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__,
    static_folder=os.path.join(BASE_DIR, '..', 'static'),
    static_url_path='/static')
```

症状：HTML加载正常但CSS/JS 404，浏览器控制台报错。

## ASN.1 解码错误分类模式

在 decode 入口统一捕获异常并分类：

```python
DECODE_ERR_FORMAT = "format_error"      # ⚠️ 数据格式错误
DECODE_ERR_NOT_LI = "not_li_message"    # 🚫 非LI报文
DECODE_ERR_UNKNOWN = "decode_failed"    # ❌ 其他异常

def _try_decode(company, payload):
    try:
        result = asn1tools.decode(...)
    except ValueError as e:
        return {'_decode_error': True, '_error_type': DECODE_ERR_FORMAT, ...}
    except Exception as e:
        if any(kw in str(e).lower() for kw in ['required', 'invalid', 'decode', 'not enough', 'type']):
            return {'_decode_error': True, '_error_type': DECODE_ERR_NOT_LI, ...}
        return {'_decode_error': True, '_error_type': DECODE_ERR_UNKNOWN, ...}
```

错误字典透传：在 `decode_pcap_payload()` 中判断 `isinstance(d, dict) and d.get('_decode_error')` 后跳过后处理。

## VERSION_HISTORY.md 版本管理

项目 `docs/` 下放版本历史，格式：

- `## V3.1 (日期)` → ### 新增 / 变更 / 修复 / 项目维护
- 版本号同步更新：app.py 注释/日志、HTML title/navbar/footer 共 3-5 处

## dpkt 命名冲突陷阱（KeyError: slice）

dpkt 的 `Packet` 类改写了 `__getitem__`，用字符串 key 访问报文头字段。当把一个 bytes/数据变量命名为 `data` 时，如果它在某个上下文中被 dpkt 的 Packet 对象覆盖或混淆，**`data[offset:]` 切片操作会触发 `Packet.__getitem__(slice(...))` → `KeyError`**。

**症状：** `KeyError: slice(14, None, None)`，堆栈指向 dpkt 而非你的代码。

**根因：** `dpkt.Packet.__getitem__(k)` 检查 `isinstance(k, str)`，切片是 slice 对象不是 str，直接 `raise KeyError(k)`。

**修复方案：**
1. 避免将 dpkt 处理过的变量命名为 `data`（使用 `payload`/`raw_buf`）
2. 传给解码函数前确保用 `bytes()` 显式转换：
   ```python
   payload = bytes(tcp.data)  # 而非 tcp.data
   ```
3. 在 pcap 解析函数内局部 import dpkt，避免全局污染

## 版本号升级 — 需同步的位置清单

小版本升级（V3→V3.1）时同步以下位置：

| 位置 | 文件 |
|------|------|
| 模块注释 | `src/app_linux_v3.py` 第2行 |
| 日志输出（3处） | `src/app_linux_v3.py` logger.info |
| HTML title | 所有模板 (`upload.html`/`result.html`/`result1.html`/`result2.html`) |
| HTML navbar h1 | 同上 |
| HTML footer | `upload.html` 页脚 |
| 版本历史 | `docs/VERSION_HISTORY.md` |
| ASN.1 规范注释 | `src/asn_spec_v3.py` 第2行 |

## GitHub 推送（GFW 环境）

```bash
https_proxy=http://127.0.0.1:7897 git clone/push/pull ...
```
