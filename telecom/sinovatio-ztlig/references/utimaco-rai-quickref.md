# Utimaco LIMS RAI 命令速查

见 `knowledge/hi2/厂商对接/Utimaco_LIMS_RAI_v16.1_协议规范.md`

## 常用命令模板

### ICD 管理
```
icdadd lea=LeaId fileref=FileRef doo=YYYYMMDD start=YYYYMMDDhhmm stop=YYYYMMDDhhmm class=0..4
icdact icd=UemRefno
icdmod icd=UemRefno stop=NOW doo=YYYYMMDD
icddel icd=UemRefno
icdreport icd=UemRefno [final]
icdlist [icd=UemRefno] [status=NP AIC]
```

### Target 管理
```
tadd icd=XXX tno=目标号码 ttype=MSISDN/IMSI/IMEI liid=XXX net=GSM,GPRS dtype=VOICE,IRI mc_voice=X mc_iri=X doo=YYYYMMDD
tlist [icd=XXX] [tno=XXX*]
tdel tno_id=XXX doo=YYYYMMDD
tmod tno_id=XXX [参数] doo=YYYYMMDD
  liid="" 清空LIID, mc_data=none 禁用数据MC
tstate icd=XXX tno=目标号码 doo=YYYYMMDD
tnelist neid=NEID_1,NEID_2
```

### MC 管理
```
mcadd lea=LeaId mctype=FTP ipaddr=a.b.c.d user=xxx pwd=xxx dir=/path
mcadd lea=LeaId mctype=ISDN isdn=号码 cugilc=xxx cugdnic=xxx
mcadd lea=LeaId mctype=TCP ipaddr=a.b.c.d port=xxx keepalive=yes dataloss=yes
mcdel mc=MCId
mcmod mc=MCId pwd=新密码
mclist [mc=MCId] [lea=LeaId]
```

### NE 管理
```
nelist [neid=NEId] [provider=ProviderId]
neadd neid=NEId netype=xxx osversion=N status=ADMIN param8=IP:port
nedel neid=NEId
nemod neid=NEId osversion=N param8=IP:port
necheck [check_only=yes] neid=NEIdList [icd=XXX tno=目标号码]
nepurge neid=NEIdList
```

### 用户/LEA 管理
```
userlist [userid=xxx]
useradd userid=xxx username=xxx password=xxx usertype=A/O/K lea=LeaId functions=0
usermod userid=xxx password=新密码
userdel userid=xxx
lealist [lea=xxx]
leaadd lea=xxx leaname=xxx maxtno=500 icddur=12
leamod lea=xxx maxtno=1500
leadel lea=xxx
```

### 审计日志
```
backuplog [from=YYYYMMDD] [to=YYYYMMDD]
functionlog [from=YYYYMMDD] [to=YYYYMMDD] [user=xxx]
loginlog [from=YYYYMMDD] [to=YYYYMMDD] [user=xxx]
```

## 关键转义/特殊值
- `liid=""` — 清空LI标识(tmod)
- `mc_data=none` — 禁用数据MC(tmod)
- `stop=NOW` — 立即停止ICD(icdmod)
- `check_only=yes` — 仅检查不修复(necheck)
- `all` — 跨LEA查看所有(限于特殊权限)
