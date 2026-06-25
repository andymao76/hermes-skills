# 华为 LI X 接口错误/返回码汇总

> 本参考文件汇总了华为 LI 相关文档中出现的所有错误码体系，用于 pcap 解码和协议排错时的快速查表。

## 1. 华为 MSC/mAGCF LIG Return Code（操作级）

华为 MSC（移动交换中心）/ mAGCF（移动接入网关控制功能）LIG 接口操作返回码，共 27 种。

| Return Code | 名称 | 说明 |
|:-----------:|------|------|
| 0 | success | 操作成功 |
| 1 | breakwithdevice | 与网元 NE 的连接中断 |
| 2 | numtypenotsupport | 号码类型不支持 |
| 3 | leaidnotcorrect | LEAID 不正确 |
| 4 | started | LEAID 已启动 |
| 5 | overtop | LEAID 数量已达上限 |
| 6 | closed | LEAID 已关闭 |
| 7 | notexist | LEAID 不存在 |
| 8 | invalidUserNameorpwd | 用户名或密码无效 |
| 9 | invalidneid | 网元 ID 无效 |
| 10 | invalidnumtype | 号码类型无效 |
| 11 | invalidnumber | 号码无效 |
| 12 | invalidtracemode | 跟踪模式无效 |
| 13 | invaliddataoutputmode | 数据输出模式无效 |
| 14 | invalidspeechoutputmode | 语音输出模式无效 |
| 15 | numberalreadyactive | 号码已激活 |
| 16 | numbernotactive | 号码未激活 |
| 17 | breakwithlig | 与 LIG 通信中断 |
| 18 | invalidate | 日期无效 |
| 19 | authenticationFailed | 认证失败 |
| 20 | userNumberNotExist | 用户号码不存在 |
| 21 | monitorNumberNotExist | 被监控号码不存在 |
| 22 | monitorNumber | 被监控号码已设置 |
| 23 | noMoniNum | 没有被监控号码 |
| 24 | parameterError | 参数错误 |
| 25 | resourceLimited | 资源受限 |
| 26 | timerOut | 定时器超时 |
| 255 | otherReason | 其他原因 |

### 分类速查

| 类别 | 码值 |
|------|------|
| 成功 | 0 |
| 连接故障 | 1, 17 |
| 认证与标识 | 3, 8, 9, 19 |
| 号码/目标相关 | 2, 10, 11, 15, 16, 20~23 |
| LEAID 状态 | 4~7 |
| 配置参数 | 12~14, 18, 24 |
| 系统资源 | 25, 26, 255 |

## 2. 华为 EPC/SAE X1 Cause（内层协议级）

定义于 `hw_epc.asn`（SAE/EPC LIG 格式，3G R8），共 26 种。

| Cause | 名称 | 说明 |
|:-----:|------|------|
| 128 | requestAccepted | 请求已接受 |
| 129 | neRestarted | NE 中 LI 功能已重启 |
| 192 | authenticationFailed | 认证失败 |
| 193 | systemFailure | 系统故障 |
| 194 | systemBusy | 系统忙 |
| 195 | mandatoryIeIncorrect | 必选 IE 错误 |
| 196 | mandatoryIeMissing | 必选 IE 缺失 |
| 197 | optionalIeIncorrect | 可选 IE 错误 |
| 198 | invalidMessageFormat | 无效消息格式 |
| 199 | addingNodeIdentityIsOccupied | 节点 ID 已被占用 |
| 200 | modifyingOrRemovingNodeIdentityDoesNotExist | 节点 ID 不存在 |
| 201 | removingNodeIsReferenced | 节点被引用 |
| 202 | noLinkResourceAvailable | 链路资源不可用 |
| 203 | incorrectStatus | 状态不正确 |
| 205 | targetNotFounded | 目标未找到 |
| 206 | undefinedHi2InterfaceId | HI2 接口 ID 未定义 |
| 207 | undefinedMonitorCenterNumber | 监控中心编号未定义 |
| 208 | unreasonableEndDate | 结束日期不合理 |
| 209 | noSystemResourceForMoreTargets | 系统资源不足 |
| 210 | iAIdIsNotConfigured | IA ID 未配置 |
| 211 | partialItemsFail | 部分项目失败 |
| 212 | tableFull | 表已满 |
| 213 | liOIdNotFound | LIOID 未找到 |
| 214 | theTargetIdIsOccupied | 目标 ID 已被占用 |
| 215 | networkElementNotSupport | 网元不支持 |
| 216 | editionError | 版本参数错误 |
| 217 | tNETypeError | TNE 类型错误 |
| 219 | targetIdTypeNotSupport | 目标 ID 类型不支持 |
| 220 | connectionExist | 连接已存在 |
| 221 | configurationLimitation | 配置限制 |

### Cause 编码范围
| 范围 | 含义 |
|:----:|------|
| 0~127 | 保留将来使用 |
| 128~191 | 成功类（128=成功, 129=重启通知） |
| 192~255 | 错误类 |

### 两套错误码的对应关系

pcap 解码时可能同时遇到这两个码值体系：

| 场景 | LIG RC（外层操作） | EPC Cause（内层响应） |
|-----|-------------------|---------------------|
| 成功 | 0 success | 128 requestAccepted |
| 认证失败 | 19 authenticationFailed | 192 authenticationFailed |
| 目标已占用 | 15 numberalreadyactive | 214 theTargetIdIsOccupied |
| 目标不存在 | 20 userNumberNotExist | 205 targetNotFounded / 213 liOIdNotFound |
| 资源受限 | 25 resourceLimited | 209 noSystemResourceForMoreTargets |
| 网元不支持 | — | 215 networkElementNotSupport |
| 版本错误 | — | 216 editionError |
| 连接断开 | 1 breakwithdevice | 220 connectionExist |
