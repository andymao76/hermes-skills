# PCAP 解码工作流 — TCP 重组与端口过滤

## 为什么要 TCP 重组？

TCP 会把大消息切成小片（Segment）发送。以太网 MSS 通常为 1460 字节，而华为 X2 口的 HI2 消息通常几百到几千字节，因此一个完整消息会被切成多个 TCP Segment。

```
TCP 分片示例（单个 HI2 消息 3300 字节）：
  [包1] TCP Seq=1000, Len=1460    ← 前 1460 字节
  [包2] TCP Seq=2460, Len=1460    ← 中间 1460 字节
  [包3] TCP Seq=3920, Len=380     ← 最后 380 字节
```

**不重组时：**
- 包1 → BER 声明长度 2000 > 1460 → 报文格式错误 ❌
- 包2 → 起始字节不是 BER TAG → 解码失败 ❌
- 包3 → 同理 → 解码失败 ❌

**重组后：** 3 个分片拼回 3300 字节完整消息 → BER 解码成功 ✅

## 实测数据对比

| 配置 | a8b0f01b (7.6MB) | c8381c8b (11.5MB) |
|------|-------------------|-------------------|
| 无TCP重组 + 无端口过滤 | 34,047 包 → 全部失败 ❌ → 57MB 页面卡死 | 52,098 包 → 全部失败 ❌ → 89MB 页面卡死 |
| **TCP重组 + 端口8890** | **61 包 → 60 成功 ✅ → 432KB** | **62 包 → 61 成功 ✅ → 407KB** |

## 端口过滤脚本（Python dpkt）

```python
import dpkt, os

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

# 用法
filter_pcap_by_port("input.pcap", "output_port8890.pcap", 8890)
```

效果：7.6MB → 96KB（压缩 98.8%），解码包数从 34,047 降至 61。

## 用户界面偏好（用于设计和迭代工具 UI）

从用户反馈中收集的 UI 偏好：
- 过滤条件标注从「可选」改为「必选」（红色标记）—— 用户需要明确区分必填/选填项，模糊的可选项会导致忘记配置
- 端口输入框标签从「X2 口建议 8890」改为「X2 口端口 例如8890」—— 用户不喜欢「建议」这类模糊措辞，要直接给具体指令+示例
- 表单项标签要精确、可操作，不要模糊/可选的语气

## X 接口日志的端口号参考

| 厂商 | 接口 | 端口 |
|------|------|------|
| 华为 IMS | X2 (IRI) | 8890 TCP |
| 华为 IMS | X3 (CC) | 9904/9905 UDP |
| 华为 IMS | 统计/心跳 | 9904/9905 UDP |
| 华为 IMS | X3 媒体 | 20000/20002/20004 UDP |
| 华为 CS | X2 | 9904/9905 |
| 中兴 EPC | X2 | 8890 |
