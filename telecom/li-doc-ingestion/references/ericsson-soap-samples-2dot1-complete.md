# Ericsson LI SOAP 完整样本集快捷参考 (2dot1)

5 个样本文件，覆盖完整 Warrant CRUD 生命周期。

## 样本文件

| # | 文件 | 操作 | type | CRUD | 路径 |
|---|------|------|:----:|:----:|------|
| 1 | Ericsson_LI_Login_SOAP_Sample_2dot1 | login | 无 | — | `li/Ericsson/` |
| 2 | Ericsson_LI_createWarrant_SOAP_Sample_2dot1 | createWarrant | 1 | C | `li/Ericsson/` |
| 3 | Ericsson_LI_getWarrantList_SOAP_Sample_2dot1 | getWarrantList | 3 | R | `li/Ericsson/` |
| 4 | Ericsson_LI_modifyWarrant_SOAP_Sample_2dot1 | modifyWarrant | 4 | U | `li/Ericsson/` |
| 5 | Ericsson_LI_deleteWarrant_SOAP_Sample_2dot1 | deleteWarrant | 2 | D | `li/Ericsson/` |

## type.__value 映射（完整 CRUD）

| 值 | CRUD | 含义 | 操作 |
|:---:|:----:|------|------|
| 1 | C | Create | createWarrant |
| 2 | D | Delete | deleteWarrant |
| 3 | R | Read/Query | getWarrantList |
| 4 | U | Update/Modify | modifyWarrant |

## 五样本对比

| 维度 | login | createWarrant | getWarrantList | modifyWarrant | deleteWarrant |
|------|-------|---------------|----------------|---------------|---------------|
| Service | SessionService | WarrantService | WarrantService | WarrantService | WarrantService |
| type.__value | 无 header | **1** | **3** | **4** | **2** |
| warrantID | — | **-1**(系统分配) | -1(不按ID过滤) | 已有ID(如62136) | 已有ID(如83978) |
| 关键入参 | userName+password | targetNumber+neGroupName+**dtlWarrants** | filterDetails+listInformation | 需修改字段+**dtlWarrants** | warrantID+targetNumber(**无dtlWarrants**) |
| 关键出参 | sessionID | warrantID | warrantItem[].state/status | responseCode | responseCode |
| 额外结构 | 无 | dtlWarrants | listInformation+orderArray | dtlWarrants | **无dtlWarrants(最简)** |

## 完整工作流

```
1. Login → sessionID + availableFunctions
2. createWarrant (warrantID=-1, targetNumber, dtlWarrants...) → warrantID
3. getWarrantList (targetNumber) → state=ACTIVATED  ← 确认设控
   ===== 可选: 修改参数 =====
4a. modifyWarrant (warrantID, MUID, mcnbs, HI2Lemf...) → 参数更新
   ===== 解控: terminate → delete =====
4b. modifyWarrant (warrantID, state=terminated) → 等待 MSC
5.  sleep 3s
6. getWarrantList (warrantID) → state=TERMINATED  ← 确认终止
7. deleteWarrant (warrantID, targetNumber) → 删除成功
8. Logout
```
