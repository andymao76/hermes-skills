---
name: remote-desktop-troubleshooting
description: "Ubuntu 远程桌面故障排查：gnome-remote-desktop (RDP) & NoMachine 及 xrdp 的安装、配置、诊断和修复"
version: 1.1.0
author: agent-created
tags: [ubuntu, rdp, nomachine, xrdp, remote-desktop, gnome, wayland, freerdp, nla, headless]
---

# Ubuntu 远程桌面故障排查

Ubuntu 24.04 远程桌面方案：系统原生 gnome-remote-desktop（RDP）、NoMachine 备用、xrdp 经典方案。涵盖 Wayland 下的安装、配置、认证问题排查。

## 触发条件

- 用户用 Windows mstsc 连接 Ubuntu 收到身份验证错误
- 用户报告 RDP 连接失败 / 断开
- 需要配置或启用远程桌面服务
- 需要在 Wayland 环境下支持远程桌面
- NoMachine / xrdp 安装与配置

**致命陷阱**：用户说「连不上」时，必须**先加载本 skill 并按步骤诊断**。跳过诊断直接给方案、画架构图、或推荐软件是常见错误。本 skill 已有完整的诊断流程和错误信号对照表——不使用它等于白写了这份 skill。

---

## 零、MUST DO：按顺序诊断，不要跳过

**用户说 "连不上" 时，禁止直接给方案或画架构图。先做以下诊断。**

### 步骤 0：确认用户说的是哪台机器（Ubuntu 服务器端）

用户可能反馈的是 "Windows 连不上"，但问题大概率在 **Ubuntu 服务器端** 而不是客户端。**禁止在跳过诊断的情况下直接给方案、画架构图或推荐软件。** 先查 Ubuntu 端，再查 Windows 端。

**核心原则：用户说「连不上」时，先找证据，再给方案。** 按顺序执行以下步骤，不要跳步。

**已被用户反复纠正过的错误模式**：

1. 「用户说远程连不上 → 直接画架构图或给软件推荐（如 NoMachine/RustDesk）→ 用户说「不对，先检查网络和端口」」。**禁止重犯。** 即使你知道最终解决方案可能是什么（如 NoMachine），也必须先做端口监听检查、服务状态确认、日志查看三步，再把结果呈现给用户。

2. **用户说「你给的办法是错的」** — 说明你在没做第一步诊断的情况下就给了方案。用户明确要求的排查顺序是：**先检查 3389 是否监听 → 检查 Windows 能否通端口 → 检查防火墙 → 检查 grd 日志**。不按这个顺序给方案，就是跳过诊断。

**正确流程**（用户已明确要求的顺序）：
```
第1步：ss -lntp | grep 3389    ← 先看端口在不在监听
第2步：Test-NetConnection ... -Port 3389  ← 再看网络能不能通
第3步：sudo ufw status / iptables -L    ← 再看防火墙拦没拦
第4步：journalctl/grdctl status          ← 再看服务/日志
第5步：只有以上都查完了，才能给方案
```
**任何一步都没做就直接给方案的行为，已经被用户明确纠正过了。**

### 步骤 1：检查端口是否在监听

```bash
ss -lntp | grep -E '(3389|4000)'
```

期望输出：
```
LISTEN 0  xxx  0.0.0.0:3389  0.0.0.0:*    # gnome-remote-desktop / xrdp
LISTEN 0  xxx  0.0.0.0:4000  0.0.0.0:*    # NoMachine
```

如果 3389 没监听，直接跳到 [第五节：无显示器的 RDP 配置](#五无显示器的-rdp-配置)。

### 步骤 2：确认是哪个进程在监听 3389

```bash
ps aux | grep -E "(grd|gnome-remote|xrdp|pipewire)" | grep -v grep
```

- `gnome-remote-desktop-daemon` → gnome-remote-desktop
- `xrdp` → xrdp 方案
- 都不是 → 可能是其他服务冒充

### 步骤 3：检查 RDP 服务状态

```bash
# daemon 级别（系统服务）
ps aux | grep gnome-remote-desktop-daemon

# systemd user 级别
systemctl --user status gnome-remote-desktop.service 2>/dev/null

# grdctl 配置状态
grdctl status
```

**注意**：`gnome-remote-desktop-daemon --system` 以 root 运行，`grdctl status` 是用户级命令。两者都可能跑，但 `--system` 模式更常见于 headless/自动登录场景。journal 日志也可能有证书警告但不一定致命。

### 步骤 4：检查日志

**注意：不要只看端口监听，日志中可能有关键错误信号。**

```bash
# RDP 日志
journalctl --user -u gnome-remote-desktop --no-pager -n 50
# 或系统日志
journalctl -u gnome-remote-desktop.service --no-pager -n 50

# NoMachine 日志
journalctl -u nxserver.service --no-pager -n 50
```

**关键信号**：
- `RDP server certificate is invalid` — 证书问题，但不一定致命，服务仍可能启动
- `Cannot load libcuda.so.1` / `libnvidia-encode.so.1` — 无 NVIDIA GPU，正常
- `RDP TLS certificate and key not yet configured properly` — 证书未就绪，服务可能启动后随即停止
- `authentication failure; rhost=192.168.x.x user=xxx` — NoMachine 有客户端的认证失败，说明网络连通但认证不对

### 步骤 5：检查 Windows 端能否通 Ubuntu 的 3389

```bash
# 在 Ubuntu 上自测？
nc -zv localhost 3389

# 更推荐的是让用户在 Windows 上运行：
# Test-NetConnection <ubuntu-ip> -Port 3389
```

### 步骤 6：检查防火墙

```bash
# ufw 状态（可能需要 sudo）
sudo ufw status

# iptables 规则
iptables -L INPUT -n -v 2>/dev/null
```

空输出 = 无自定义防火墙规则。

---

## 一、服务状态快速诊断

### 1. 查看当前桌面会话类型

```bash
echo $XDG_SESSION_TYPE
loginctl show-session $(loginctl list-sessions --no-legend | awk '{print $1}') -p Type
```

Ubuntu 24.04 默认使用 **Wayland**，这对远程桌面兼容性有影响。

### 2. 检查远程桌面服务

```bash
# gnome-remote-desktop-daemon（系统原生）
systemctl status gnome-remote-desktop.service
ps aux | grep gnome-remote-desktop-daemon

# xrdp（如果安装过）
systemctl status xrdp
systemctl status xrdp-sesman

# 检查监听端口
ss -tlnp | grep -E '3389|4000'
```

### 3. 查看 RDP 状态（gnome-remote-desktop）

```bash
grdctl status
```

输出示例：
```
RDP:
    Status: enabled          # 未启用
    Port: 3389
    TLS certificate: /home/.../rdp-tls.crt
    View-only: no
    Negotiate port: yes
```

### 4. 查看服务日志

```bash
journalctl -u gnome-remote-desktop.service --no-pager -n 40
```

---

## 二、关键错误场景：Windows mstsc "身份验证错误"

### 错误表现

Windows mstsc 连接 Ubuntu 时弹出：
> 发生身份验证错误。有更多数据可用
> 远程计算机: 192.168.x.x

同时 gnome-remote-desktop 日志中出现：
```
[ERROR][com.winpr.sspi.NTLM] - [ntlm_read_AuthenticateMessage]: MIC verification failed!
[WARN][com.winpr.sspi] - AcceptSecurityContext status SEC_E_MESSAGE_ALTERED [0x8009030F]
[ERROR][com.freerdp.core.connection] - server supports only NLA Security
[ERROR][com.freerdp.core.connection] - Protocol security negotiation failure
```

### 根本原因

gnome-remote-desktop 使用 **FreeRDP 的 NTLM 实现**，与 Windows 某些版本的 mstsc CredSSP NLA 协商时，**消息完整性校验（MIC）失败**。这是 FreeRDP 已知兼容性问题。

服务端日志中 "server supports only NLA Security" 表明服务端仅接受 NLA 认证，但 Windows 客户端的 NLA 协商数据包被 FreeRDP 解析为 "被篡改"。

### 修复方法：Windows 注册表

在 **Windows 客户端机器** 上，以管理员身份运行：

```powershell
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System\CredSSP\Parameters" /v AllowEncryptionOracle /t REG_DWORD /d 2 /f
```

或者导入注册表文件（.reg）：

```ini
Windows Registry Editor Version 5.00

[HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System\CredSSP\Parameters]
"AllowEncryptionOracle"=dword:00000002
```

**参数说明：**
- `AllowEncryptionOracle=2` — 强制 Windows 客户端使用最宽松的 NLA 加密协商模式，兼容 FreeRDP 服务端
- 安全层面：内网/家庭环境中安全可用
- 修改后重启 mstsc 即可，无需重启 Windows

### 如果注册表修复无效

如果 `AllowEncryptionOracle=2` 后 Windows mstsc 仍然报同样的错误，依次尝试：

1. **试试值 0** — 更保守的兼容模式
   ```powershell
   reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System\CredSSP\Parameters" /v AllowEncryptionOracle /t REG_DWORD /d 0 /f
   ```

2. **从组策略禁用 NLA 要求**（需 Windows Pro/Enterprise）
   - 运行 `gpedit.msc`
   - 计算机配置 → 管理模板 → Windows 组件 → 远程桌面服务 → 远程桌面会话主机 → 安全
   - 设置 **"远程(RDP)连接要求使用指定的安全层"** 为 **"RDP"**（不使用 SSL/TLS）
   - 设置 **"要求使用网络级别的身份验证对远程连接进行用户身份验证"** 为 **"已禁用"**

3. **换用其他 RDP 客户端** — Windows Store 版 Microsoft Remote Desktop、Royal TS、Remote Desktop Manager 等第三方 RDP 客户端可能绕开此问题

4. **彻底放弃 RDP，使用 NoMachine** — 如果以上都无效且 NoMachine 能正常工作，直接使用 NoMachine 是最省心的方案

### 验证修复

```bash
# 在 Ubuntu 端确认 RDP 端口在监听
ss -tlnp | grep 3389

# 检查防火墙
sudo ufw status
sudo iptables -L INPUT -n --line-numbers | grep 3389
```

---

## 三、启用 gnome-remote-desktop RDP

### 启用 RDP 服务

```bash
# 启用 RDP
grdctl rdp enable

# 设置认证凭据
grdctl rdp set-credentials <用户名> <密码>
```

### 验证

```bash
grdctl status
ss -tlnp | grep 3389
```

### 已知问题

| 问题 | 原因 | 解决 |
|------|------|------|
| 启用后 3389 未监听 | 服务未启动 | `sudo systemctl restart gnome-remote-desktop.service` |
| 密码错误 | grdctl rdp set-credentials 格式 | 正确格式：`grdctl rdp set-credentials <用户名> <密码>`（两个参数，用户名和密码分开，不要只有 username） |
| 连接后闪退 | Wayland 会话问题 | 检查 `journalctl -u gnome-remote-desktop.service` |
| Windows 连接报"凭证不工作" | RDP 密码与用户密码不同步 | 确保使用当前登录用户的密码 |
| `grdctl rdp get-credentials` 不存在 | grdctl 版本差异 | 某些版本无此子命令，用 `grdctl status` 看凭据状态即可 |
| journal 中 `RDP server certificate is invalid` | 首次启动时证书自签过程中临时错误 | 通常自动恢复，检查证书文件是否有效：`openssl x509 -in <crt> -text -noout` |
| `gnome-remote-desktop-daemon --system` 模式 | grdctl 是用户级命令；`--system` daemon 以 root 运行，两者都可能存在但独立管理 | 即使 `systemctl --user status gnome-remote-desktop.service` 显示 masked，系统 daemon 仍可能正常工作（`ps aux | grep gnome-remote-desktop-daemon` 确认） |

---

## 四、NoMachine 方案（推荐作为主/备用）

NoMachine 是 Ubuntu 远程桌面的**推荐备用方案**，尤其在 RDP 存在兼容性问题时。相比 RDP 的优势：不依赖显示管理器状态、穿越能力强、Wayland 支持好。

### 安装

```bash
# 下载 NoMachine for Linux (x86_64)
curl -L -o nomachine.deb "https://download.nomachine.com/download/8.16/Linux/nomachine_8.16.1_1_amd64.deb"

# 安装
sudo dpkg -i nomachine.deb

# 验证
systemctl status nxserver.service
```

### 常用命令

```bash
# 查看服务状态
systemctl status nxserver.service

# 是否接受新连接
/usr/NX/bin/nxserver --status

# 查看连接日志
journalctl -u nxserver.service --no-pager -n 50
```

### 认证失败的日志信号

NoMachine 认证失败会在 journal 中记录为：
```
pam_unix(nx:auth): authentication failure; logname= uid=123 euid=0 tty= ruser= rhost=192.168.x.x  user=andymao
```

这表明：
- 网络连通性 ✅（请求已经到达 Ubuntu）
- 端口 4000 正常 ✅
- 认证凭据 ❌（密码错误）

**诊断意义**：看到 `rhost=<IP>` 即可确认客户端能到达服务器，问题不在网络而在认证。可据此排除网络层故障。

### 优点

| 特性 | RDP (gnome-remote-desktop) | NoMachine |
|------|---------------------------|-----------|
| Wayland 支持 | 原生 | ✅ 良好 |
| Windows 客户端兼容 | ⚠️ 有 NTLM 兼容问题 | ✅ 稳定 |
| 剪贴板共享 | 有限 | ✅ 完整 |
| 文件传输 | 有限 | ✅ 内置 |
| 音视频重定向 | 有限 | ✅ 良好 |
| 性能 | 一般 | ✅ 优秀 |
| 安装包大小 | 系统内置 | ~40MB |
| 无显示器 headless | 需配置 | ✅ 原生支持 |

---

## 五、无显示器的 RDP 配置 (headless)

在没有物理显示器的机器（headless 服务器）上使用 gnome-remote-desktop，可能遇到服务启动后无法建立会话的问题。

### 检查当前会话

```bash
loginctl list-sessions
loginctl show-session <session_id> -p Type,Display,Remote
```

期望看到一个 `type=wayland`（或 `x11`）且 `remote=no` 的本地会话。如果没有，说明没有可用的图形会话让 RDP 连接。

### 解决 headless 无会话问题

1. **确认系统显示管理器（GDM）正在运行并创建了会话**
   ```bash
   systemctl status gdm3
   ```

2. **如果启用了自动登录，确认用户已登录到本地 tty**
   ```bash
   loginctl list-sessions | grep seat0
   ```

3. **如果完全没有图形会话，RDP 将无法正常工作** — 此时 NoMachine 是最佳替代方案

---

## 六、xrdp 方案（备选）

xrdp 是经典方案，但在 Ubuntu 24.04 Wayland 下需要额外配置。

### 安装

```bash
sudo apt update
sudo apt install -y xrdp
sudo systemctl enable --now xrdp
```

### Wayland 兼容说明

Ubuntu 24.04 默认 Wayland，xrdp 默认只支持 Xorg 会话。可以使用以下变通方案：

**方案 A：安装 xorgxrdp**
```bash
sudo apt install -y xorgxrdp
```
然后在登录界面选择 Xorg 会话。

**方案 B：使用 XRDP 的 Xorg 后端**
```bash
# 配置 xrdp 使用 Xorg
sudo sed -i 's/use_vsock=.*/use_vsock=false/' /etc/xrdp/xrdp.ini
sudo systemctl restart xrdp
```

**方案 C：切换登录会话为 Xorg**
```bash
sudo sed -i 's/#WaylandEnable=false/WaylandEnable=false/' /etc/gdm3/custom.conf
```
修改后需重启或重新登录。

---

## 七、常见问题排查表

| 症状 | 可能原因 | 排查步骤 | 解决 |
|------|---------|---------|------|
| mstsc 报"身份验证错误" | FreeRDP NTLM MIC 校验失败 | 检查 gnome-remote-desktop 日志 | Windows 端改注册表 AllowEncryptionOracle=2 |
| 连接后黑屏 | Wayland 兼容性问题 | `echo $XDG_SESSION_TYPE` | 切换到 Xorg 或改用 NoMachine |
| 3389 端口未监听 | gnome-remote-desktop 未启动 | `grdctl status` | `sudo systemctl restart gnome-remote-desktop.service` |
| 3389 未监听且 grdctl 显示 enabled | 证书初始化失败或 headless 无会话 | 检查 journal + loginctl | 重新生成证书或使用 NoMachine |
| 连接被拒绝 | 防火墙阻挡 | `ufw status` | `sudo ufw allow 3389` |
| NoMachine 连接后立即断开 | 认证问题或版本不匹配 | `journalctl -u nxserver.service` | 检查认证失败的 IP，更新 NoMachine 客户端 |
| NoMachine 日志有认证失败但端口正常 | 客户端密码错误 | journal 日志中有 `authentication failure; rhost=<ip>` | 在客户端确认密码 |
| xrdp 连接失败 | Wayland 不支持 xrdp | `systemctl status xrdp` | 切换到 Xorg 或安装 xorgxrdp |
| RDP 连接超时（200ms+） | 代理环境变量影响 | 检查浏览器工具的 proxy env | 本机直连不依赖代理 |
| 窗口闪烁/刷新慢 | RDP 图形驱动 | 换 NoMachine | 使用 NoMachine 的 GPU 加速 |

---

## 参考

- `references/gnome-remote-desktop-ntlm-fix.md` — NTLM MIC 校验失败详细信息与注册表修复步骤
