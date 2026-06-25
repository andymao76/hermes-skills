# Utimaco LIMS RAI CLI 速查

完整笔记：`~/knowledge/hi2/厂商对接/Utimaco_LIMS_RAI_v16.1_协议规范.md`

## 常用目标操作

```bash
tadd icd=00302 tno=0031223 ttype=MSISDN liid=223 net=GSM dtype=VOICE,IRI mc_voice=2 mc_iri=27 doo=20020730
tlist icd=00302
tdel tno_id=1 doo=20020228           # 无输出
tmod tno_id=1 mcflags=423 area=1,4 doo=20100404
tstate icd=00302 tno=0031223 doo=20020730  # 无输出
tnelist neid=NOLI_1,NOCS_1           # 非确定性结果
```

## MC 操作

```bash
mclist mc=34
mcadd lea="Lea1" mctype=FTP ipaddr=192.168.23.112 user=anonymous pwd=anonymous dir=/srec
mcdel mc=23
mcmod mc=23 pwd=1q2w3e4r
```

## NE 操作

```bash
nelist neid=DF2
neadd neid=UTVF_1 netype=utvf osversion=2 param8=127.0.0.1:64743
nedel neid=UTVF_1
nemod neid=UTVF_1 osversion=1 param8=127.0.0.1:11111
necheck neid=DF2
nepurge neid=NOCS18_0                # 需 PURGE_NODE 许可
```

## ICD 生命周期

```bash
icdadd lea=auth1 fileref="case1" doo=20260618 start=202606180000 stop=202606302359 class=3
icdact icd=00302
icddel icd=00302
icdmod icd=00302 stop=NOW doo=20260618
icdreport icd=00302 [final]
```

## 用户/LEA

```bash
useradd userid=o1 username=Operator1 password=aysx6z7u usertype=O state=active lea=Lea1 functions=0
userdel userid=o1
usermod userid=o1 password=1q2w3e4r
leaadd lea=auth1 leaname=Authority1 maxtno=500 icddur=30 country=0
```

## RAI-SP 会话结构

TCP 端口 52134。
LOGIN PDU: Type=1, 固定 126 字节 (user 21 + pwd 16 + newpwd 16 + version 4 + utcflag 1)
REPLY PDU: Type=5 (CES 4 + CEI 101 + output 可变)
密码规则: 8-15 字符, 至少 2 字母 + 2 数字, 无简单序列
