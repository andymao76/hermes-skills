# gnome-remote-desktop NTLM MIC 校验失败修复记录

## 错误日志原文

从 `journalctl -u gnome-remote-desktop.service --no-pager -n 40` 获取：

```
[WARN][com.winpr.sspi] - [winpr_AcceptSecurityContext]: AcceptSecurityContext status SEC_E_MESSAGE_ALTERED [0x8009030F]
[ERROR][com.freerdp.core.auth] - [credssp_auth_authenticate]: AcceptSecurityContext failed with SEC_E_MESSAGE_ALTERED [0x8009030F]
[ERROR][com.freerdp.core.transport] - [transport_accept_nla]: client authentication failure
[ERROR][com.freerdp.core.peer] - [peer_recv_callback_internal]: CONNECTION_STATE_NEGO - rdp_server_accept_nego() fail
[ERROR][com.freerdp.core.transport] - [transport_check_fds]: transport_check_fds: transport->ReceiveCallback() - STATE_RUN_FAILED [-1]
[RDP] Network or intentional disconnect, stopping session
[WARN][com.freerdp.core.connection] - [rdp_server_accept_nego]: server supports only NLA Security
[ERROR][com.freerdp.core.connection] - [rdp_server_accept_nego]: Protocol security negotiation failure
[ERROR][com.freerdp.core.transport] - [transport_default_write]: BIO_should_retry returned a system error 32: Broken pipe
[ERROR][com.freerdp.core.peer] - [transport_default_write]: ERRCONNECT_CONNECT_TRANSPORT_FAILED [0x0002000D]
[ERROR][com.winpr.sspi.NTLM] - [ntlm_read_AuthenticateMessage]: Message Integrity Check (MIC) verification failed!
```

## 错误码解释

| 错误码 | 含义 | 说明 |
|--------|------|------|
| SEC_E_MESSAGE_ALTERED [0x8009030F] | 消息完整性校验失败 | Windows 客户端发送的 NLA 数据包被 FreeRDP 认为"被篡改"，实际是 NTLM 实现差异 |
| MIC verification failed | MIC 验证失败 | NTLM AuthenticateMessage 中的 MIC（消息完整性校验）字段与 FreeRDP 的计算结果不一致 |
| server supports only NLA Security | 服务端仅接受 NLA | gnome-remote-desktop 强制要求网络级身份认证，不支持旧版 RDP 安全层 |
| ERRCONNECT_CONNECT_TRANSPORT_FAILED [0x0002000D] | 传输层连接失败 | 认证协商失败后管道断开 |

## 环境信息

| 项目 | 值 |
|------|-----|
| Ubuntu 版本 | 24.04.4 LTS (Noble) |
| 显示服务器 | Wayland |
| 桌面环境 | GNOME Shell (Ubuntu session) |
| 远程桌面服务 | gnome-remote-desktop-daemon (FreeRDP 后端) |
| RDP 端口 | 3389 (0.0.0.0:3389) |
| 防火墙 | ufw 未启用 |
| 客户端 | Windows mstsc |
| 备用方案 | NoMachine 正常工作 |

## Windows 注册表修复（首选）

```powershell
# 管理员 PowerShell
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System\CredSSP\Parameters" /v AllowEncryptionOracle /t REG_DWORD /d 2 /f
```

修复后无需重启 Windows，重启 mstsc 即可。

## 注册表修复后仍然无效时的逐步排查

### 步骤 1：试试 AllowEncryptionOracle=0

```powershell
# 更保守的兼容模式
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System\CredSSP\Parameters" /v AllowEncryptionOracle /t REG_DWORD /d 0 /f
```

### 步骤 2：组策略中禁用 NLA 要求（Windows Pro/Enterprise）

运行 `gpedit.msc` → 计算机配置 → 管理模板 → Windows 组件 → 远程桌面服务 → 远程桌面会话主机 → 安全：
- 设置 "远程(RDP)连接要求使用指定的安全层" 为 **"RDP"**
- 设置 "要求使用网络级别的身份验证对远程连接进行用户身份验证" 为 **"已禁用"**

### 步骤 3：换用其他 RDP 客户端

Windows 自带 mstsc 的 CredSSP 实现与 FreeRDP 存在版本差异。尝试：
- **Microsoft Remote Desktop**（Windows Store 版）
- **Royal TS**
- **Remote Desktop Manager**

### 步骤 4：回到 NoMachine

如果以上都不行，NoMachine 始终能正常工作。用 NoMachine 是最省心的方案。

## 关键事实

- NoMachine 的 NX 协议不受此问题影响，始终可用
- Ubuntu 24.04 自动登录用户如果未单独设置密码，RDP 认证也可能失败（检查 `passwd --status <user>`）
- gnome-remote-desktop 的 FreeRDP 后端不支持通过配置禁用 NLA（不能降级到 TLS-only），所以所有 NLA 问题都只能从客户端侧解决
- 用 nc 测试 RDP 端口连通性：`echo -ne '\x03\x00\x00\x13\x0e\xe0\x00\x00\x00\x00\x00\x01\x00\x08\x00\x03\x00\x00\x00' | nc -w 3 <host> 3389 | xxd | head -5`
