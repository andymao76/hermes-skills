# Ericsson LI SOAP 请求样本参考 (2dot1)

路径: `~/knowledge/li/Ericsson/`

## Login 样本

| 项目 | 值 |
|------|-----|
| 文件 | `Ericsson_LI_Login_SOAP_Sample_2dot1.md` |
| namespace | `http://session.bind.external.ws2dot1.ims.epa.ericsson.se/` |
| SOAP Action | `urn:Login` |
| Endpoint | `/ws2dot1/services/SessionServicePort` |
| 关键参数 | userName(NissAdmin) + password(Niss1234) |
| 成功返回 | status.__value=3, sessionID, availableFunctions |
| 前置依赖 | 无（第一步） |

**结构:** `login → arg0(sessionRequest) → userName + password`

## createWarrant 样本

| 项目 | 值 |
|------|-----|
| 文件 | `Ericsson_LI_createWarrant_SOAP_Sample_2dot1.md` |
| namespace | `http://warrant.bind.external.ws2dot1.ims.epa.ericsson.se/` |
| SOAP Action | `urn:CreateWarrant` |
| Endpoint | `/ws2dot1/services/WarrantServicePort` |
| 关键参数 | warrantID=-1, targetNumber=251970751036, targetTypeID=MSISDN, neGroupName=NeGrp1 |
| 成功返回 | responseCode.__value=3, warrantID(如37890) |
| 前置依赖 | 需先 login 获取 sessionID |

**结构:** `createWarrant → arg0(warrantCreateRequest) → header(requestHeader) + item(warrantItem) + dtlWarrants(dtlWarrantNeTypeItemArray)`

## 完整设控→解控工作流

```
1. Login → sessionID
2. createWarrant(warrantID=-1, targetNumber, neGroupName, dtlWarrants...)
     → warrantID (如 37890)
3. getWarrantList(warrantID) → 查看状态
4. modifyWarrant(warrantID, state=terminated) → 终止
5. sleep 3s → 等待 LIIMS 与 MSC 交互
6. deleteWarrant(warrantID, targetNumber) → 删除
7. Logout
```

## 关联文档

- `Ericsson_LI-IMS_登录返回状态码.md` — login 返回码 1-12
- `爱立信CURL对接整理.md` — curl 实操流程
- `爱立信1口对接调试文档.md` — WSDL+XSD 构建步骤
- `爱立信-HI1结构一览及其构造-详细.md` — 字段取值详解
- `Ericsson_IMS_LI_External_API_WebServices_R6A.md` — 服务矩阵

## 版本差异 (2dot1 → 16A)

| 项目 | 2dot1 | 16A |
|------|-------|-----|
| session namespace | `session.bind.external.ws2dot1` | `session.bind.external.ws16a` |
| warrant namespace | `warrant.bind.external.ws2dot1` | `warrant.bind.external.ws16a` |
| userName 类型 | limitedStringType | xs:string |
| 额外 import | limitedstring_schema.xsd | 无 |
