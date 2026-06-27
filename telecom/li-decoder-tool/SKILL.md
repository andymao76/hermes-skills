---
name: li-decoder-tool
description: ETSI-ASN1-Assistant LI 解码工具 — PCAP 解码/X 接口日志分析/BER 解码器使用、正确配置、常见错误排查。覆盖 12 种解码模式选择、TCP 重组原理、端口过滤、大文件处理。
category: telecom
tags: [li-decoder, pcap, x-interface, ber, hi2, etsi-asn1]
---

# ETSI ASN.1 Assistant LI 解码工具 (v4.0.1+)

ETSI-ASN1-Assistant 是 LI X2/X3/HI1 接口解码器 Web 工具，部署在 `~/projects/ETSI-ASN1-Assistant/`，支持 12 种解码模式 + X 接口日志分析。

项目位置：`~/projects/ETSI-ASN1-Assistant/`
GitHub：`github.com/andymao76/ops-monitoring`（V4 分支）
知识库：`~/knowledge/telecom/lawful_interception/etsi-asn1-assistant-usage-guide.md`

## 一、触发条件

- 用户提及 LI 解码、PCAP 解码、HI2 解码、IRI 报告
- 用户提及 ETSI-ASN1-Assistant、解码器、解码失败
- 用户提及 X 接口日志、ZTLIG1 日志分析
- 用户上传 .pcap 文件需解码
- 用户遇到「报文格式错误」「解码失败」错误

## 二、快速启动

```bash
cd ~/projects/ETSI-ASN1-Assistant
source venv/bin/activate
python3 src/app_linux_v4.py
# 浏览器访问 http://127.0.0.1:5000
```

## 三、PCAP 解码正确步骤

### 必选配置

1. **勾选「TCP 重组」** — TCP 会把大消息切成 1460 字节的分片发送。不重组时每个分片被独立解码，全部失败
2. **输入端口过滤** — 只解码 X2 口数据：
   - 华为 IMS X2 口 → `8890`
   - 华为 CS X2 口 → `9904` / `9905`
   - 中兴 EPC X2 口 → `8890`
3. **选择解码模式**（见第五节）

### TCP 重组原理

以太网 MSS 通常为 1460 字节，而 HI2 消息通常 2000~5000 字节，因此会被 TCP 切成多个 Segment：

```
[包1] Seq=1000, Len=1460   ← HI2 消息前 1460 字节
[包2] Seq=2460, Len=1460   ← 中间 1460 字节
[包3] Seq=3920, Len=380    ← 最后 380 字节
```

**不重组 → 每个分片独立解码 → 全部失败**（包1 BER 长度 > 数据长度、包2/3 起始非 BER TAG）
**重组后 → 拼回完整 3300 字节消息 → 解码成功**

### 用户输出偏好

向用户报告 PCAP 测试结果时，使用**对比表**格式展示「无配置」vs「正确配置」的实际数据差异：

```
| 配置 | a8b0f01b (7.6MB) |
|------|-------------------|
| 无重组+无端口过滤 | 34,047 包, 全部失败 |
| TCP重组+端口8890  | 61 包, 60 成功 ✅  |
```

### X 接口日志分析

ETSI-ASN1-Assistant V4.0.1 支持四种日志类型上传分析，专用路由 `/x-interface`。接口类型必须手工选择（X1/X2/X3），**没有「自动识别」选项**。

### 支持的日志类型

| 日志类型 | 接口 | 文件名特征 | 说明 |
|---------|------|-----------|------|
| ZTLIG1 | X1 管理面 | `ztlig1*.txt` | 设控/停控/网元通信日志，14 种命令识别 |
| ZTLIG2 | X2 信令面 | `ztlig2*.txt` | IRI CDR JSON 日志 |
| SSF | X2 SIP 信令 | `ssf*.txt` | SIP 会话管理日志 |
| RVF | X3 RTP 媒体 | `rvf*.txt` | RTP 媒体流日志 |

### 综合分析报告（四种类型通用）

上传后自动生成综合分析报告，包含：

**ZTLIG1 特有章节：**
- 子模块负载分布（ztlig-1_web 71%、ztlig-1_hwne 22%、ztlig1-db 3% 等）
- 14 种 X1 操作统计（redis_sync/link_check/set_target/ne_no_response 等）
- 设控/停控统计（Kafka 消息次数 + 去重 LIID 数）
- 网元通信故障（连接检查失败/链路错误/网元无响应 + 故障 NE Top10）
- 关键样本 8 类（Kafka设控消息/DB设控成功/网元响应/X1发送结果/Hi1队列反馈/网元无响应/ERROR样本）

**通用章节（所有类型）：**
- 概览（时间范围、总行数、ERROR、LIID、分析耗时）
- LIID Top15
- 关键样本（默认展开）
- **🔍 关键发现** — 自动生成观察结论（活跃 LIID 占比、高 401 拒绝率、心跳失败检测等）

**ZTLIG2 特有：** EventDetail 分布、LigCdr 数量
**SSF 特有：** SIP 方法分布（INVITE/BYE/200/401 等，**带占比列**）、CallID 数量
**RVF 特有：** CorrelationID 数量、RTP 会话数、媒体类型分布

### 使用方法

1. 在 `/x-interface` 页面上传 `.txt` 文件
2. **手工选择接口类型**（X1/X2/X3，无自动识别）
3. 选择子类型（ZTLIG1/SSF/ZTLIG2/RVF）
4. 点击「分析」→ 立即显示「⏳分析中...」加载状态（含文件名和大小）
5. 分析完成后展示：综合分析报告（顶部卡片）+ 左栏摘要 + 右栏原始日志预览
6. 分析耗时和文件大小在统计卡中显示（包括「⚠️大文件」标签）
7. 如需输出，点击「📥 输出 Markdown 报告」按钮下载完整报告

**报告内容：**
- **通用**：概览（时间范围、总行数、ERROR、LIID、分析耗时）、LIID Top15、关键样本（默认展开）
- **ZTLIG1 特有**：子模块分布、14 种 X1 操作统计、设控/停控、网元故障（NE 级详情）、8 类命名样本
- **SSF 特有**：SIP 方法分布（带占比列）、CallID 数量
- **ZTLIG2 特有**：EventDetail 分布、LigCdr 数量
- **RVF 特有**：CorrelationID 数量、RTP 会话数、媒体类型分布
- **🔍 关键发现**：自动生成观察结论（活跃 LIID 占比、高 401 拒绝率、心跳失败检测等）

**注意事项：**
- 分析结果左栏为「**摘要模式**」（按命令/操作分组显示关键信息+样本），不再渲染逐行日志
- 右栏原始日志仅显示前 1000 行（大文件时）
- 导出按钮只支持 **Markdown** 格式（已移除 HTML 导出）
- 大文件分析时，`FileReader.readAsText(blob)` 读取前 10MB 避免浏览器阻塞

### 大文件处理（V4.0.1 已实现）

生产日志可达数 GB（如 ztlig1.300.txt 521MB/473万行）。V4.0.1 移除 5MB 前端截断，改为报告驱动模式：

- **前端**：`FileReader.readAsText()` 异步读取，大文件(>10MB)仅读取前 10MB（避免浏览器卡死）
- **后端**：全量解析收到的内容，无 size 限制
- **文件 >5MB 时**：只返回报告 + 左栏摘要(5000条) + 右栏原始日志预览(1000行) +「⚠️大文件」标签
- **文件 ≤5MB 时**：全量返回（向后兼容）
- **加载提示**：选择文件后立即显示「⏳分析中...」状态，包含文件名、大小、读取提示
- **按钮反馈**：点击分析后按钮立即禁用（`btn.disabled = true`），文字依次变化：`▶ 分析 → ⏳ 分析中... → 📤 上传分析中... → ▶ 分析`（恢复）。防止重复点击，即使 JS 出错用户也知道已触发
- **进度步骤**：展示分步进度（`📂 文件读取中 → 📤 上传分析中 → 🔄 后端处理中 → 📊 生成报告`），每步完成后标记 ✅
- **分析耗时**：后端计时返回 `analysis_time`，统计卡中显示「分析耗时」卡片
- **关键发现**：自动生成 🔍 关键发现卡片（活跃LIID占比、高401拒绝率、心跳失败检测等）
- **常见陷阱**：
  - `blob.text()` 在某些浏览器中不可用，改用 `FileReader.readAsText()` 保证兼容性
  - `.catch()` 中不要调用未定义的函数（如 `analyzeComplete()`），否则 ReferenceError 导致静默失败
  - `showLoading()` 中 **不能使用 `el.querySelector('.card')`** — `#emptyState` 元素内无 `.card` 子元素，.card只存在其他区域。必须直接用 `el.innerHTML` 替换整个 emptyState 内容。否则 TypeError 中断整个 analyzeFile() 函数，按钮无反应

## 五、10 种解码模式

| 模式 | 适用场景 | 厂商 |
|------|---------|------|
| hw-cs | 电路交换 IRI | 华为 MSC/MGW |
| hw-ims | VoLTE/VoWiFi IRI | 华为 SBC/CSCF |
| zte-cs | 电路交换 IRI | 中兴 |
| mavenir | XML 格式 IRI | Mavenir |
| g2k | PS 域 IRI | G2K |
| utimaco-volte | VoLTE IRI | Utimaco |
| hw-5gc | 5GC X2 接口 | 华为 |
| hw-sae | SAE/LTE X2 接口 | 华为 |
| nsn-cs | 电路交换 IRI | 诺西 |
| zte-epc | EPC X2 接口 | 中兴 |

注：主页面解码模式从 12 种减为 10 种（V4.0.1 移除了 x3 和 hi1）。x3→X接口日志 RVF 页面，hi1→X接口日志 ZTLIG1 页面。

## 六、常见错误与排查

### 表现 → 根因 → 解决

| 现象 | 根因 | 解决 |
|------|------|------|
| 大量「报文格式错误」⚠️ | TCP SYN/ACK/HTTP 等非 X2 口包被尝试解码 | 输入端口过滤 `8890` |
| 大量「解码失败」❌ | TCP 分片未重组，每片独立解码 | 勾选「TCP 重组」 |
| 页面 57~89MB 浏览器卡死/崩溃 | 无过滤导致全量网络包全部解码+渲染 | 端口过滤即可降至 <500KB |
| 0xAA 帧头红色 warning | 检测到华为帧头但 TCP 重组未开 | 勾选「TCP 重组」后重新上传 |
| curl 正常但浏览器不通过 | 旧 Flask 进程仍在运行，新代码未生效 | `lsof -i :5000` 查 PID → `kill` |
| 选择 IRI 上传日志文件 | 文本日志不是 BER 十六进制格式 | 应在「X 接口日志」页面或 IR 口上传 |
| 大文件无反映（浏览器卡死） | FileReader.readAsText 阻塞 UI 线程 | `FileReader.readAsText(blob)` 读取前 10MB, 大文件仅读前 10MB |

### 导出按钮（仅 Markdown）

- 导出报告**只支持 Markdown 格式**（已移除 HTML 导出）
- 点击「📥 输出 Markdown 报告」下载 `.md` 文件
- 报告内容：概览/子模块分布/操作统计/LIID/设控停控/网元故障/关键样本
- 文件 >5MB 时导出的是综合报告摘要（非原始逐行数据）

### 服务部署陷阱

| 陷阱 | 说明 | 排查/修复 |
|------|------|----------|
| 旧进程残留 | 旧 `app_linux_v4.py` 仍绑定 5000 端口。新进程因端口冲突启动失败静默退出，curl 实际访问旧服务 | `lsof -i :5000` 查 PID → `kill` |
| bg venv 失效 | `background=true` 启动的进程未激活 venv，import 报错 | 用绝对路径 `/path/venv/bin/python3` + 设置 `workdir` |
| 修改后未重启 | 修改 `x_interface_decoder.py` 或模板后，Flask 不会热重载 | kill 旧进程 → 重新启动 |

## 七、PCAP 端口过滤脚本

使用 Python dpkt 从 PCAP 过滤指定端口的包，大幅减小文件体积：

```python
import dpkt
def filter_pcap_by_port(in_path, out_path, target_port):
    with open(in_path, 'rb') as f:
        reader = dpkt.pcap.Reader(f)
        writer = dpkt.pcap.Writer(open(out_path, 'wb'))
        for ts, buf in reader:
            eth = dpkt.ethernet.Ethernet(buf)
            if not isinstance(eth.data, dpkt.ip.IP): continue
            ip = eth.data
            if not isinstance(ip.data, dpkt.tcp.TCP): continue
            tcp = ip.data
            if tcp.sport == target_port or tcp.dport == target_port:
                writer.writepkt(buf, ts)
```

典型效果：7.6MB PCAP → 96KB（压缩 98.8%），解码包数从 34,047 降至 61。

## 八、设计文档维护

功能变更（尤其是架构级改造）后必须同步更新系统设计文档：

```
docs/ETSI_ASN1_Assistant_V4_系统设计文档.md
```

更新位置：
- **新功能/架构变更** → 对应章节新增子节（如 8.3 大文件处理方案）
- **删除功能** → 从相关章节移除引用
- **配置/接口变更** → 更新接口描述

更新后 commit 时在 message 中注明文档变更。

## 九、验证清单

- [ ] 解码前先确认：TCP 重组勾选了？端口过滤输对了？解码模式选对了？
- [ ] 修改代码后确认旧进程已杀死、新进程已启动（`lsof -i :5000` + curl 测试）
- [ ] X 接口日志上传前确认文件类型正确（ztlig1 不是 BER hex）
- [ ] 大文件用前 5MB 测试，确认解析质量后再处理完整文件
- [ ] 修改 `x_interface_decoder.py` 后运 test 脚本验证 13 个单行用例

## 九、关联技能

- `zte-li` — ZTLIG 系统运维（ztlig1/ztlig2/ssf/rvf）
- `ber-tlv-analysis` — BER TLV 码流分析
- `etsi-lawful-intercept` — ETSI LI 标准体系
- `hw-li` — 华为 LI 全栈
