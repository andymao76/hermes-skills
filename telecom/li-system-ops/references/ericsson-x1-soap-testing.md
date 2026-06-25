# Ericsson IMS LI X1 SOAP 接口测试参考

## 环境

- **Mock 服务器**: http://localhost:19090
- **SessionService**: http://localhost:19090/SessionServicePort
- **WarrantService**: http://localhost:19090/WarrantServicePort
- **命名空间**: `http://session.bind.external.ws1dot8.ims.epa.ericsson.se/` (Session)
- **命名空间**: `http://warrant.bind.external.ws1dot8.ims.epa.ericsson.se/` (Warrant)
- **SOAPAction**: `urn:Login`, `urn:CreateWarrant`, `urn:GetWarrantList`, `urn:DeleteWarrant`
- **响应码**: 3=SUCCESS, 0=BUSINESS_RULE_VIOLATION, 1=INTERNAL_ERROR, 2=INVALID_SESSION

## 完整 curl 测试模板

### 1. Login

```bash
curl -s -X POST http://localhost:19090/SessionServicePort \
  -H "Content-Type: text/xml;charset=UTF-8" \
  -H "SOAPAction: urn:Login" \
  -d '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                        xmlns:sess="http://session.bind.external.ws1dot8.ims.epa.ericsson.se/">
   <soapenv:Header/>
   <soapenv:Body>
      <sess:login>
         <arg0>
            <userName>admin</userName>
            <password>password123</password>
         </arg0>
      </sess:login>
   </soapenv:Body>
</soapenv:Envelope>'
```

返回：
```xml
<ns2:loginResponse>
  <return>
    <status><__value>0</__value></status>
    <sessionID>SESS-ABC123XYZ-20260618</sessionID>
    <roleID>ADMIN</roleID>
    <ldapEnabled>false</ldapEnabled>
  </return>
</ns2:loginResponse>
```

### 2. CreateWarrant (X1 初始化核心)

```bash
curl -s -X POST http://localhost:19090/WarrantServicePort \
  -H "Content-Type: text/xml;charset=UTF-8" \
  -H "SOAPAction: urn:CreateWarrant" \
  -d '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                        xmlns:war="http://warrant.bind.external.ws1dot8.ims.epa.ericsson.se/">
   <soapenv:Header/>
   <soapenv:Body>
      <war:createWarrant>
         <arg0>
            <header>
               <type><__value>1</__value></type>
               <userID>admin</userID>
               <sessionID>SESS-ABC123XYZ-20260618</sessionID>
            </header>
            <item>
               <warrantID>-1</warrantID>            <!-- -1 = 新建 -->
               <targetNumber>8612345678900</targetNumber>
               <targetTypeID>1</targetTypeID>
               <neName>MGW-01</neName>
               <lea>LEA_BEIJING</lea>
               <MUID>MUID-20260618-001</MUID>
               <useOneLemf>1</useOneLemf>
               <lemf>10.20.30.40:6000</lemf>
               <isTargetPABX>false</isTargetPABX>
               <legalBasis>Criminal Procedure Law Art.116</legalBasis>
               <acc>ACC-001</acc>
               <subnetOperatorID>CHN-MOBILE</subnetOperatorID>
               <netOperatorID>CHN-MOBILE</netOperatorID>
               <caseID>CASE-2026-001</caseID>
               <isTargetNumberSuppressed>false</isTargetNumberSuppressed>
               <activationTime>1787011200000</activationTime>
               <terminationTime>1818547200000</terminationTime>
               <userID>admin</userID>
               <supplementaryInfo>0</supplementaryInfo>
               <GGSNMonitoring>false</GGSNMonitoring>
               <positioningPeriod>-1</positioningPeriod>  <!-- -1=禁用定位 -->
               <radiusWarrantId>-1</radiusWarrantId>
            </item>
            <dtlWarrants>
               <item>
                  <warrantID>-1</warrantID>
                  <neType>MSC</neType>
                  <isDataMonitoringOnly>0</isDataMonitoringOnly>
                  <targetInfo>0</targetInfo>
               </item>
               <item>
                  <warrantID>-1</warrantID>
                  <neType>SIPSERVER</neType>
                  <isDataMonitoringOnly>0</isDataMonitoringOnly>
                  <targetInfo>0</targetInfo>
               </item>
               <item>
                  <warrantID>-1</warrantID>
                  <neType>GPRS</neType>
                  <isDataMonitoringOnly>1</isDataMonitoringOnly>
                  <targetInfo>0</targetInfo>
               </item>
            </dtlWarrants>
         </arg0>
      </war:createWarrant>
   </soapenv:Body>
</soapenv:Envelope>'
```

返回：
```xml
<ns2:createWarrantResponse>
  <return>
    <code><__value>3</__value></code>
    <reason>SUCCESS</reason>
    <objectId>10001</objectId>
  </return>
</ns2:createWarrantResponse>
```

### 3. GetWarrantList

```bash
curl -s -X POST http://localhost:19090/WarrantServicePort \
  -H "Content-Type: text/xml;charset=UTF-8" \
  -H "SOAPAction: urn:GetWarrantList" \
  -d '<soapenv:Envelope...><war:getWarrantList>
      <arg0><header><type><__value>3</__value></type>
      <userID>admin</userID><sessionID>SESS-...</sessionID></header></arg0>
    </war:getWarrantList></soapenv:Body></soapenv:Envelope>'
```

返回 warrant 列表，包含所有 targetNumber 等字段。

### 4. DeleteWarrant

```bash
curl -s -X POST http://localhost:19090/WarrantServicePort \
  -H "Content-Type: text/xml;charset=UTF-8" \
  -H "SOAPAction: urn:DeleteWarrant" \
  -d '<soapenv:Envelope...><war:deleteWarrant>
      <arg0><header><type><__value>2</__value></type>
      <userID>admin</userID><sessionID>SESS-...</sessionID></header>
      <item><warrantID>10001</warrantID></item></arg0>
    </war:deleteWarrant></soapenv:Body></soapenv:Envelope>'
```

返回：code=3 SUCCESS。

## Python Mock 服务器

位于 `/tmp/ericsson-li-mock.py`，模拟所有四个 SOAP 操作。启动：

```bash
python3 /tmp/ericsson-li-mock.py &
# 输出: [EricssonLI-Mock] Starting on port 19090
```

Mock 日志会打印接收到的 SOAP 请求信息（SOAPAction、targetNumber、caseID、NE types 等）。

## SoapUI 项目文件

- **完整 WSDL 绑定版（GUI）**: `/home/andymao/SmartBear/ericsson-x1-init.xml`
- **WSDL 文件目录**: `/home/andymao/SmartBear/x1-test/`（含 sessionservice.wsdl, warrantservice.wsdl, 所有 xsd）
- **Groovy 脚本版（参考）**: `/tmp/x1-groovy-test.xml`

> ⚠️ SoapUI 5.10.0 testrunner 在命令行模式下无法创建测试步骤（xsi:type 实例化失败），导致 TestSteps=0。建议 GUI 使用 + curl 命令行验证的组合方式。
