# 中兴 ZTE V3/V4 LIS 网元返回状态码

中兴 LIS（Lawful Interception System）V3/V4 版本网元操作返回码，共 17 种。

| Return Code | 含义 |
|:-----------:|------|
| 0 | success |
| 1 | target has existed |
| 2 | target does not exist |
| 3 | MC does not exist |
| 4 | parameters input incorrectly |
| 101 | no power to operation |
| 2001 | same liid target exists |
| 2002 | liid format fail (digits only) |
| 2003 | TI format fail |
| 2005~2008 | SD/ST/ED/ET format fail |
| 2009 | TT format fail |
| 2010 | need LIID or TT+TI |

# 爱立信 Ericsson LI-IMS 登录返回状态码

爱立信 LI-IMS 系统登录接口返回码，共 12 种。

| Return Code | 含义 |
|:-----------:|------|
| 1 | account locked |
| 2 | login failed (generic) |
| 3 | login successful |
| 4 | logout failed |
| 5 | logout successful |
| 6 | first login, must change default password |
| 7 | password expired (validity period) |
| 8 | new password not strong enough |
| 9 | new password recently used |
| 10 | invalid session |
| 11 | invalid license |
| 12 | invalid LDAP license |

# 三家厂商错误码对比

| 场景 | 华为 MSC/mAGCF | 中兴 ZTE V3/V4 | 爱立信 LI-IMS |
|:----:|:--------------:|:--------------:|:--------------:|
| 成功 | 0 | 0 | 3(登录)/5(登出) |
| 认证失败 | 19 | — | 2 |
| 密码问题 | 8 invalidUserName | — | 6(首次)/7(过期)/8(弱)/9(重复) |
| 账户锁定 | — | — | 1 |
| 无权限 | — | 101 | 10(会话)/11(许可证) |
| 参数错误 | 24 | 4 / 2002~2009 | — |

详细文档见 `~/knowledge/research/` 下的独立 md 文件。
