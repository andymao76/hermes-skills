# Ericsson LI-IMS SOAP 2dot1 — 5 操作综合参考

## CRUD type.__value 编码

| 值 | CRUD | SOAP Action | 操作 | 请求结构 |
|:---:|:----:|:-----------:|------|---------|
| **1** | Create | urn:CreateWarrant | createWarrant | header + item(warrantItem) + dtlWarrants |
| **2** | Delete | urn:DeleteWarrant | deleteWarrant | header + item(warrantItem) **无 dtlWarrants** |
| **3** | Read | urn:GetWarrantList | getWarrantList | header + listInformation + filterDetails + orderArray |
| **4** | Update | urn:ModifyWarrant | modifyWarrant | header + item(warrantItem) + dtlWarrants |

## 操作对比

| 维度 | login | createWarrant | getWarrantList | modifyWarrant | deleteWarrant |
|------|-------|---------------|----------------|---------------|---------------|
| Service | SessionService | WarrantService | WarrantService | WarrantService | WarrantService |
| 关键入参 | userName + password | warrantID=**-1**, targetNumber, dtlWarrants | targetNumber + 分页 + 排序 | warrantID=**已有ID**, 修改字段 | warrantID=已有ID, targetNumber |
| 关键出参 | sessionID | warrantID(系统分配) | warrantItem数组(state/status) | responseCode | responseCode |
| dtlWarrants | 无 | 必填(定义各NE参数) | 无 | 可填(更新dtl参数) | 无 |

## 完整工作流

```
Login → sessionID
createWarrant (warrantID=-1, targetNumber, neGroupName, dtlWarrants...) → warrantID
getWarrantList (targetNumber) → state=ACTIVATED, status=INPROGRESS
  [可选] modifyWarrant (warrantID, MUID, mcnbs, ...) → 参数更新
modifyWarrant (warrantID, state=terminated) → ⚠ 需sleep 3s
getWarrantList (warrantID) → state=TERMINATED ✓
deleteWarrant (warrantID, targetNumber) → 解控成功
Logout
```

## 请求/响应关键字段

**requestHeader:** type.__value(Create=1/Delete=2/Read=3/Update=4), userID, sessionID

**warrantItem 关键字段:** warrantID(-1=新建), targetNumber, targetTypeID(MSISDN/IMSI/IMEI/E.164/VoLTE/SIP-URI), neGroupName, LEA, caseID, activationTime(0=立即), terminationTime(毫秒时间戳), supplementaryInfo(bitmask定位授权), dtID(VCE-1/DFA-1), sfID(HOI/DDE/IOBS), positioningPeriod(-1/5/15/30/45/60), GGSNMonitoring

**dtlWarrantNeTypeItem:** warrantID(-1), neType(MSC/GPRS/SIPSERVER/HLR/5GCORE...), HI2Lemf, isDataMonitoringOnly(0=IRI+CC/1=仅IRI), mcnbs(int数组)

**listInformation (查询分页):** recordsOnThisPage(请求=0), maxRecordsPerPage(请求时设), pageNumber(从1开始), totalPages(请求=-1)

**orderArray:** listElementIdentifier(0=WARRANT_ID,其他常量见properties文件), orderDirection.__value(1=ASC/2=DESC)

## sessionID 规则

- login 成功后返回，有效期 **5 分钟**
- 超时后需重新 login
- 作为字符串注入到后续每个 SOAP 请求的 `header.sessionID`
- sessionID 字符串可能含特殊字符（如 `T8az;pybc3vuO+uz2,F8`）

## Error 说明

| 场景 | 现象 |
|------|------|
| 创建时 warrantID 不填 -1 | 系统拒绝 |
| Terminate 前直接 delete | **失败**（必须先 terminate + 等3s） |
| sessionID 过期 | **RemoteServerException** |
| 用户无权限 | login 返回的 availableFunctions 中不含所需操作 |

## 已知对接配置

| 参数 | 值 |
|------|-----|
| 端口 | 8443 |
| Endpoint | `/ws2dot1/services/{ServiceName}Port` |
| 命名空间(2dot1) | `http://{service}.bind.external.ws2dot1.ims.epa.ericsson.se/` |
| Content-Type | `application/soap+xml` |
| X1 IP | 在 ztlig.cfg 中逐厂商配置 |
| 厂商代码(ztlig) | `ericlis24` |
