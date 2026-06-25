# 语音处理架构速查（STCMS/MSVRS + TMC + TSPS + SICMS）

详见 `knowledge/li/projects/STCMS-MSVRS/voice-processing-architecture.md`

## 系统对比

| 系统 | 转码 | 实时 | 录播 | 格式 |
|------|------|------|------|------|
| STCMS/MSVRS | TPF | Kafka PCMA流 | 格式一→TPF→格式三 | 格式一(私有) |
| TMC | RVF | X3口 TDM/IP | 直接播PCMA | 直PCMA不带头 |
| TSPS | VDC | — | 私有→VDC→WAV | 私有原始 |
| SICMS | 播放器内置 | × | 播放器内转码 | 原始编解码 |

## 语音文件格式

| 格式 | 头 | 帧 |
|------|----|----|
| 格式一 | 32B(NAP2)+帧头(9B) | 变长原始编码 |
| 格式二(废弃) | 256B(全0) | 160B固定PCMA, 50fps |
| 格式三 | 44B(WAV RIFF) | 160B固定PCMA, 50fps |

## 声纹匹配

- 实时: Flink→TPF转码→声扬(38870)→GP
- 历史: Web创建→Kafka→historyvoice_transcode→historyvoice_match→GP
- 阈值: 60分 TOP10
- License: 默认10声纹库
