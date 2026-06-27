# Mavenir LI 分析命令速查

## 归档包分析

```bash
# 列出/解压XMLSpy项目
7z l archive.7z
7z x archive.7z -y
cat IMS-LI.spp                             # 项目文件结构

# 提取XSD约束关键词
grep -E "minLength|maxLength|pattern|enumeration|restriction" *.xsd

# 检查DTD引用
grep -r "DOCTYPE" *.xml --no-filename | sort -u
```

## X2 Base64 SIP Payload 解码

```bash
# 提取并解码所有Base64 Payload
grep -oa '<!\[CDATA\[[A-Za-z0-9+/=]*\]\]>' file.xml | \
  sed 's/<!\[CDATA\[//;s/\]\]>//' | base64 -d

# 提取X2 Return-code
grep -oa '<Return-code>[^<]*</Return-code>' file.xml | sort | uniq -c

# 提取EventPayload (Mid-Call Interception)
grep -oaP '<EventPayload>.*?</EventPayload>' file.xml | head -3
```

## X1 SOAP 设控/取消设控

```bash
# 所有SOAP操作统计
tcpdump -r pcap -A | grep -oaP "Mavenir:\w+" | sort | uniq -c

# 返回码
tcpdump -r pcap -A | grep -oaP '<ReturnCode>\d+' | sort | uniq -c

# 目标分布
tcpdump -r pcap -A | grep -oaP '<litid>\d+' | sort | uniq -c
tcpdump -r pcap -A | grep -oaP '<target>[^<]+' | sort | uniq -c
tcpdump -r pcap -A | grep -oaP '<targettype>[^<]+' | sort | uniq -c

# 交付地址
tcpdump -r pcap -A | grep -oa "deliveryfunction2\|deliveryfunction3" | sort | uniq -c
```

## ZTLIG1 日志 (X1管理面)

```bash
# 所有Mavenir X1操作
grep "MavUagX1" ztlig1.log | grep -v "GetStatus"

# 健康轮询
grep "MavUagX1GetStatus" ztlig1.log

# 错误
grep -E "actneID fail|target_notify.*fail|P_node failed" ztlig1.log
```

## X2 IRI 信令面

```bash
# SIP方法与状态码
tcpdump -r pcap -A | grep -oaE "INVITE |MESSAGE |REGISTER |NOTIFY |SUBSCRIBE |BYE |SIP/2\.0 [0-9]+" | sort | uniq -c

# Call-ID 唯一列表
tcpdump -r pcap -A | grep -oaP 'Call-ID: \S+' | sort -u

# Correlation-id
tcpdump -r pcap -A | grep -oaP '<Correlation-id>[^<]+' | sort -u

# 双li-tid检查
tcpdump -r pcap -A | grep -oaP '<li-tid>\d+' | sort | uniq -c
```

## ZTLIG2 / SSF 日志

```bash
# Mavenir子模块处理
grep "Mavenir_LIS_MsgProc" ztlig2.log

# LigCdr输出
grep "EncodeToJson.*LIID.*10078" ztlig2.log

# SSF状态机
grep "ssf_deal_sip_msg\|ssf_send_lig2_call_msg" ssf.log | grep "LIID\[10078\]"

# SSF→RVF通知
grep "ssf_send_rvf_msg" ssf.log | grep "LIID\[10078\]"
```

## X3 媒体面

```bash
# PayloadLength分布
strings pcap | grep -oP '<PayloadLength>\d+' | sort | uniq -c | sort -rn

# PayloadType确认
strings pcap | grep -oP '<PayloadType>[^<]+' | sort -u

# 双li-tid
strings pcap | grep -oP '<li-tid>\d+' | sort | uniq -c
```

## RVF 日志

```bash
# 轮询次数
grep -c "getXmlStringElement" rvf.log

# 媒体控制事件
grep "rvfMediaCommandDealThread" rvf.log

# Session管理
grep -E "rvfCreateSession|rvfFindMavenirSessionId" rvf.log
```
