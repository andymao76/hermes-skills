# nDPI — 开源深度包检测工具

> 版本: 5.1.0-1-7b43393 (编译自源码)
> 路径: `/home/andymao/nDPI/`
> 可执行: `/home/andymao/nDPI/example/ndpiReader`
> 库文件: `/home/andymao/nDPI/src/lib/libndpi.so.5.1.0`
> 测试样本: `/home/andymao/ndpi-test/samples/`

---

## 安装方式

### 源码编译 (无 sudo 权限时)

```bash
git clone --depth=1 https://github.com/ntop/nDPI.git
cd nDPI
./autogen.sh && ./configure
make -j$(nproc)
```

编译产物：
- `example/ndpiReader` — 命令行分析工具
- `src/lib/libndpi.so.5.1.0` — 共享库
- `src/lib/libndpi.a` — 静态库

### Ubuntu 包管理 (需 sudo)

```bash
sudo apt-get install libndpi-bin libndpi-dev
```

## ndpiReader 用法

```bash
# 基本使用
ndpiReader -i file.pcap

# 指定协议配置文件
ndpiReader -i file.pcap -p /path/to/protos.txt

# JSON 序列化结果
ndpiReader -i file.pcap -k output.bin -K json

# 实时抓包 60 秒
ndpiReader -i eth0 -s 60 -p protos.txt

# 列出所有支持的协议
ndpiReader -a 0

# 禁用端口/IP猜测（纯 DPI）
ndpiReader -i file.pcap -d

# 查看所有选项
ndpiReader -h
```

## 内存消耗

| 指标 | 值 |
|:----|:---:|
| 一次性内存 | 3.55 KB |
| 每流内存 | 1.28 KB |
| 小 pcap (14包) | ~9 MB 总分配 |
| 中等 pcap (1039包) | ~9 MB 总分配 |

内存消耗极低，基础分配 ~9MB 后几乎不随流量线性增长。

## 协议识别测试结果

| PCAP 文件 | nDPI 识别 | 报文数 | 说明 |
|:----------|:---------:|:------:|------|
| SIP-I (ISUP IAM) | **SIP** ✓ | 14 | VoIP 类别 |
| RTP 媒体流 | **RTP** ✓ | 1039 | Media 类别，20.76秒 |
| SIP Register | **SIP** ✓ | 1 | Register 请求 |
| SIP Call (with Proxy) | **SIP** ✓ | 3 | 完整呼叫流程 |
| SIP SDP Example | **SIP** ✓ | 1 | SDP 协商 |
| G.729 SIP+RTP | **SIP+RTP** ✓ | 433 | SIP 6包 + RTP 425包 |
| 华为 SBC LI 上报 | **Unknown** | 16 | `aa05` 封装无法穿透 |

**结论：** nDPI 对标准 SIP/RTP 协议识别准确率 100%。华为 LI 封装 (`aa05` 头部) 无法直接识别，需先用 `tcpdump` 剥离 LI 头部。

## 已知识别的电信协议

nDPI 内置 200+ 协议签名，电信相关包括：
- **VoIP**: SIP, RTP/RTCP, H.323, MGCP, MEGACO
- **信令**: DIAMETER, RADIUS
- **传输**: HTTP/2, TLS, DNS, DHCP
- **加密指纹**: JA3/JA4 TLS 指纹

## 局限

- 无法识别 `aa05` 封装的自定义协议（华为/Sinovatio LI 上报）
- 需搭配 `tcpdump` 或 Wireshark 作为 LI 数据的补充分析工具
- 不支持深度 ASN.1 PER 解码（RANAP/NGAP 需用专用解码器）
