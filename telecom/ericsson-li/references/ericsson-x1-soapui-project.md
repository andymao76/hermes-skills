# Ericsson X1 SoapUI 项目参考

## 项目结构

项目文件: `/home/andymao/SmartBear/ericsson-x1-init.xml`

包含:
- **WSDL 接口引用**: SessionService + WarrantService（引用本地 WSDL/XSD）
- **测试套件 "X1-Initialization"**: 4 个 TestCase
  - `01-Login` — SessionService.login
  - `02-CreateWarrant` — WarrantService.createWarrant（X1 初始化核心）
  - `03-GetWarrantList` — 验证创建结果
  - `04-DeleteWarrant` — 清理
- **Mock 服务**: "EricssonLI-IMS-Mock"（端口 19090）

## WSDL 配置

WSDL 文件副本: `/home/andymao/SmartBear/ericsson-x1-wsdl/`

使用前需将 WSDL 中的 `<soap:address location>` 指向目标 LI-IMS 地址。

当前测试配置指向 Mock（端口 19090）:
- `http://localhost:19090/SessionServicePort`
- `http://localhost:19090/WarrantServicePort`

## Mock 测试

### 方法 1: Python Mock（推荐，稳定可靠）

```bash
# 启动 Mock
python3 /tmp/ericsson-li-mock.py

# 在另一个终端测试
curl -s -X POST http://localhost:19090/SessionServicePort \
  -H "Content-Type: text/xml;charset=UTF-8" \
  -H "SOAPAction: urn:Login" \
  -d '<soapenv:Envelope ...><sess:login>...</sess:login></soapenv:Envelope>'
```

### 方法 2: SoapUI 内置 Mock（mockservicerunner）

SoapUI 的 `mockservicerunner` 在加载不含 WSDL 绑定的 MockOperation 时可能出现 NPE：
```
java.lang.NullPointerException: Cannot invoke "javax.wsdl.BindingOperation.getExtensibilityElements()"
```

**解决方案**: MockOperation 必须带 `interface` 和 `operation` 属性引用已加载的 WSDL 接口，
或者改用 Python Mock 这种更灵活的方式。

### 方法 3: SoapUI testrunner

```bash
bash ~/SmartBear/SoapUI-5.10.0/bin/testrunner.sh \
  -r -j -f /tmp/results \
  -s "X1-Initialization" \
  "/home/andymao/SmartBear/ericsson-x1-init.xml"
```

注意: testrunner 加载绝对路径的 WSDL 文件时，如果 XSD 引用是相对路径可能会有问题。

## 完整的 X1 初始化请求示例

### Login
```xml
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
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
</soapenv:Envelope>
```

### Login 响应（sessionID 提取用）
```xml
<sessionID>SESS-ABC123XYZ-20260618</sessionID>
```

### CreateWarrant（X1 初始化核心）
```xml
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                  xmlns:war="http://warrant.bind.external.ws1dot8.ims.epa.ericsson.se/">
   <soapenv:Header/>
   <soapenv:Body>
      <war:createWarrant>
         <arg0>
            <header>
               <type><__value>1</__value></type>   <!-- 1=CREATE -->
               <userID>admin</userID>
               <sessionID>SESS-ABC123XYZ-20260618</sessionID>
            </header>
            <item>
               <warrantID>-1</warrantID>
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
               <positioningPeriod>-1</positioningPeriod>
               <radiusWarrantId>-1</radiusWarrantId>
            </item>
            <dtlWarrants>
               <item>
                  <warrantID>-1</warrantID>
                  <neType>MSC</neType>
                  <isDataMonitoringOnly>0</isDataMonitoringOnly>   <!-- 0=IRI+CC -->
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
                  <isDataMonitoringOnly>1</isDataMonitoringOnly>   <!-- 1=仅IRI -->
                  <targetInfo>0</targetInfo>
               </item>
            </dtlWarrants>
         </arg0>
      </war:createWarrant>
   </soapenv:Body>
</soapenv:Envelope>
```

## 已知问题与排障

| 问题 | 原因 | 解决 |
|------|------|------|
| testrunner 加载 WSDL 失败 | 绝对路径导致 XSD 引用未解析 | 改用 file:// URI 或相对路径 |
| testrunner "Failed to create test step" | WSDL 接口未能加载 | 确认 WSDL+XSD 文件在同一目录 |
| Mock "WarrantServicePort" 请求报 NPE | SoapUI mock 需要 WSDL 绑定 | 用 Python mock 替代 |
| SOAP 请求 `xsi:type` 未绑定 | XML 根元素缺 xmlns:xsi 声明 | 在 con:soapui-project 根加 xmlns:xsi |
| 响应码不是 3 | 请求结构可能不符合 XSD | 检查 sessionID、warrantID=-1 |
