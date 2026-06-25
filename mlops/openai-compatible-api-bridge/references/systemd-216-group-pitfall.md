# systemd user service 216/GROUP 问题排查记录

## 现象

用户级 systemd 服务启动后立即退出，状态码 216：

```
hermes-bridge.service: Failed to determine supplementary groups: Operation not permitted
hermes-bridge.service: Main process exited, code=exited, status=216/GROUP
```

## 原因

这是 Ubuntu 22.04 (kernel 6.x) 上的已知问题。用户级 systemd `Type=simple` 服务在启动进程时尝试获取补充组列表，但由于 cgroup v2 权限限制失败。类型改为 `Type=exec` 在某些系统上有效，但不是所有发行版。

## 排查步骤

1. 检查服务状态：`systemctl --user status <service>`
2. 检查 journal：`journalctl --user -xeu <service>`
3. 确认不是依赖问题：手动运行 `ExecStart` 命令（在 shell 中执行）确认正常

## 诊断流程

当服务出现 status=216/GROUP 时，按以下步骤排查：

1. **检查 journal 获取确切错误**：
   ```bash
   journalctl --user -xeu <service> --no-pager | tail -20
   ```
   关键错误行：
   ```
   Failed to determine supplementary groups: Operation not permitted
   ```

2. **确认是 systemd 问题而非命令本身**：直接在 shell 中手动执行 `ExecStart` 命令，确认脚本/命令本身没有故障。

3. **检查 service 文件中的 `SupplementaryGroups=` 字段**：
   ```bash
   cat ~/.config/systemd/user/<service>.service | grep -n "SupplementaryGroups"
   ```
   如果有 `SupplementaryGroups=`（空值），**删除此字段**（这是最可能的原因）。

4. **如果仍有其他进程占住端口**，用 `ss -tlnp | grep <PORT>` 确认并查杀。

## 解决方案（优先级从高到低）

### 方案 A：删除空的 SupplementaryGroups= 字段 + 移除 User= 行（首选）

```bash
# 删除 SupplementaryGroups= 空行
sed -i '/^SupplementaryGroups=$/d' ~/.config/systemd/user/<service>.service
# 也删掉 User= 行——user mode systemd 不需要且可能触发相同的 216/GROUP
sed -i '/^User=/d' ~/.config/systemd/user/<service>.service
systemctl --user daemon-reload && systemctl --user restart <service>
```

空的 `SupplementaryGroups=` 在 systemd v251+ 上会触发 kernel 的 `getgroups()` 调用，而用户级服务无权执行此操作。

**关键补充：** 即使删掉了 `SupplementaryGroups` 行，如果 service 文件中还保留着 `User=andymao`（或其他用户名），某些 systemd 版本（Ubuntu 24.04 + systemd 255）仍然会报 `status=216/GROUP`。因为用户级 systemd 默认以当前用户身份运行 service，`User=` 字段在 user mode 下是多余的，且会触发同一条 supplementary groups 检查路径。**同时删除 `SupplementaryGroups=` 和 `User=` 两行才稳妥。**

验证是否解决：
```bash
systemctl --user daemon-reload
systemctl --user restart <service>
sleep 1
systemctl --user status <service> --no-pager | head -10
```

### 方案 B：使用 nohup + PID 文件替代 systemd

```bash
nohup python3 /path/to/script.py >> /path/to/log 2>&1 &
echo $! > /path/to/pidfile
```

管理脚本使用 kill + pidfile 控制生命周期。

## 不适用的方案

以下常见建议在 kernel 6.x + Ubuntu 上已验证无效：

- **`SupplementaryGroups=`（空值）**：❌ 正是触发原因，不是解决方案
- **`Type=exec`**：❌ 仍然失败（与 type 无关，是 supplementary groups lookup 的问题）
- **系统级 service**（`sudo systemctl`）：需要 root，但此问题仅发生在用户级 systemd

记忆要点：在 `~/.config/systemd/user/` 的 service 文件中，删除整行 `SupplementaryGroups=` 比留着空值更安全。Ubuntu 24.04 / kernel 6.x 系统上尤其如此。
