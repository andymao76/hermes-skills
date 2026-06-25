# Ericsson LI-IMS SOAP Login Sample — 2dot1 vs 16A 对比

> 来源: 实际对接项目分享的 SOAP 样本 (ws2dot1)
> 版本对比: WSDL/XSD 文件分析 (R4A 发布包)

---

## 实际 Login 请求 XML (2dot1)

```xml
<soapenv:Envelope
  xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
  xmlns:ses="http://session.bind.external.ws2dot1.ims.epa.ericsson.se/">
  <soapenv:Header/>
  <soapenv:Body>
    <ses:login>
      <arg0>
        <userName>NissAdmin</userName>
        <password>Niss1234</password>
      </arg0>
    </ses:login>
  </soapenv:Body>
</soapenv:Envelope>
```

**SOAP Action:** `urn:Login`
**Endpoint:** `https://<LIIMS_IP>:8443/ws2dot1/services/SessionServicePort`

---

## 响应结构 (基于 XSD)

```xml
<soapenv:Envelope ...>
  <soapenv:Body>
    <ns:loginResponse>
      <return>
        <status><__value>3</__value></status>   <!-- 返回码: 3=成功 -->
        <sessionID>/S9jCg[_:Np1t-ug<qhh</sessionID>  <!-- 后续操作需携带 -->
        <availableFunctions>WarCreate</availableFunctions>
        <availableFunctions>WarDelete</availableFunctions>
        <availableFunctions>WarMod</availableFunctions>
        <availableFunctions>WarView</availableFunctions>
        <!-- ... 完整列表见 SKILL.md -->
        <roleID>Admin</roleID>
        <ldapEnabled>false</ldapEnabled>
      </return>
    </ns:loginResponse>
  </soapenv:Body>
</soapenv:Envelope>
```

**sessionResponse 字段:**

| 字段 | 类型 | 说明 |
|------|------|------|
| status.__value | int | 返回码 (1-12) |
| sessionID | string | 会话 ID，有效期 5 分钟 |
| availableFunctions | string[] | 用户可用功能列表 |
| roleID | string | 用户角色 |
| ldapEnabled | boolean | LDAP 启用状态 |

---

## 2dot1 vs 16A Schema 差异

### 2dot1 (样本版本)

**命名空间:** `http://session.bind.external.ws2dot1.ims.epa.ericsson.se/`
**额外 import:** `limitedstring_schema.xsd` (`http://utility.bind.ws2dot1.ims.epa.ericsson.se/`)

```xml
<xs:complexType name="sessionRequest">
  <xs:sequence>
    <xs:element minOccurs="0" name="userName" type="nsx:limitedStringType" />
    <xs:element minOccurs="0" name="password">
      <xs:simpleType>
        <xs:restriction base="xs:string">
          <xs:maxLength value="160"/>
        </xs:restriction>
      </xs:simpleType>
    </xs:element>
  </xs:sequence>
</xs:complexType>
```

### 16A (最新版)

**命名空间:** `http://session.bind.external.ws16a.ims.epa.ericsson.se/`
**简化:** 无额外 import，类型改为标准 xs:string

```xml
<xs:complexType name="sessionRequest">
  <xs:sequence>
    <xs:element minOccurs="0" name="userName" type="xs:string" />
    <xs:element minOccurs="0" name="password" type="xs:string" />
  </xs:sequence>
</xs:complexType>
```

### 差异总结

| 项目 | 2dot1 | 16A |
|------|-------|-----|
| userName 类型 | `nsx:limitedStringType` (需导入 limitedstring_schema) | `xs:string` |
| password 限制 | maxLength 160 | 无限制 |
| 额外 import | limitedstring_schema.xsd | 无 |
| 异常命名空间 | `exception.ws2dot1` | `exception.ws16a` |
| 登录流程 | 完全相同 | 完全相同 |

**结论:** 协议层无差异，仅类型定义简化。SOAP 请求 XML 在 2dot1 和 16A 间可互换使用。

---

## 返回码 (sessionStatus.__value)

| 码 | 含义 | 说明 |
|:--:|------|------|
| 1 | account locked | 账户已锁定，需联系安全管理员 |
| 2 | login failed | 登录失败（通用原因） |
| **3** | **successful login** | **登录成功** |
| 4 | logout failed | 登出失败 |
| 5 | successful logout | 登出成功 |
| 6 | first time login | ImsAdmin 首次登录，需修改默认密码 |
| 7 | password validity | 密码有有效期限制 |
| 8 | password not strong | 新密码强度不足 |
| 9 | password recently used | 新密码最近使用过 |
| 10 | invalid session | 会话无效 |
| 11 | invalid license | 许可证不允许新访问 |
| 12 | invalid LDAP license | LDAP 许可证不允许 |

---

## 登录后典型流程

```
Login (userName + password)
  → sessionID + availableFunctions
  → createWarrant (warrantID=-1, targetNumber, neType, mcnbs...)
    → warrantID (系统分配)
  → getWarrantList / modifyWarrant (terminate)
  → deleteWarrant
  → Logout (sessionID)
```

> **注意:** sessionID 有效期 5 分钟，超时需重新 login。
> soap:body use="literal" — XML 元素名完全匹配 XSD 定义，`<arg0>` 是参数包装名。
