---
name: linux-system-ops
description: Linux 系统运维全集 — 磁盘管理/挂载/fstab、备份策略/rsync/cron、桌面环境配置/应用安装/输入法。
category: devops
priority: high
tags: [linux, ubuntu, disk, mount, backup, desktop, install, rsync]
---

# Linux System Operations

Ubuntu 24.04 系统运维全流程指南。涵盖磁盘管理、备份策略、桌面环境配置三大领域。

## 快速导航

| 场景 | 跳转 |
|------|------|
| 磁盘空间分析、Snap 清理、日志维护、fstab 配置 | → `references/disk-management.md` |
| 配置 rsync 备份、cron 定时任务、备份验证 | → `references/backup-strategies.md` |
| exFAT → ext4 磁盘格式转换（含完整步骤、耗时预估、后续处理） | → `references/exfat-to-ext4-conversion.md` |
| 系统盘空间分析与优化（分层分析→分类决策→批量迁移） | → `references/system-disk-optimization.md` |
| Docker 容器数据迁移到 exfat 备份盘（含模型缓存、代理配置） | → `references/docker-exfat-migration.md` |
| 安装桌面应用（shell 安装器/deb/AppImage）、Java 开发工具（SoapUI）、输入法配置 | → `references/desktop-install.md` |

---

## 通用注意事项

### ⚠️ 高危操作安全原则（必须遵守）

涉及以下操作的，**必须先获得用户明确确认**才能执行：

1. **符号链接（symlink）操作** — 不要假设断链就是"坏了需要修"。很多系统故意设计为系统盘只有符号链接，真实数据在外置备份盘。断链时正确的做法是先检查挂载状态、报告用户，而不是直接重建本地目录。
2. **系统磁盘架构变更** — 包括 fstab 修改、分区操作、目录迁移等。
3. **系统级清理/删除** — 尤其是涉及多级目录、跨挂载点的批量操作。
4. **配置文件直接修改** — config.yaml, .env 等核心配置文件。

排查路径：当发现断链时：
```
1. mountpoint 检查目标挂载点 → 未挂载则报告用户
2. ls -la 检查断链目标路径 → 确认是备份盘路径还是本地路径
3. 是备份盘路径 → sudo mount 挂载即可，不要重建本地目录
4. 用户说"帮我操作"时可直接执行，否则输出命令让用户执行
```

### sudo 在 Hermes 中的限制
Hermes 终端工具不支持交互式 sudo（无密码输入 tty）。涉及 sudo 操作时：
1. 使用 `write_file` 将内容写到 `/tmp/` 临时文件
2. 告知用户手动执行 sudo 命令
3. 或在支持的环境中使用后台/自动化脚本

### exfat 文件系统陷阱
- exfat 不支持 Unix 符号链接 → rsync 会有 symlink 警告（可忽略）；**HuggingFace 模型缓存严重依赖 symlink**，无法直接在 exfat 上工作，需单独处理（见 `references/docker-exfat-migration.md`）
- exfat 不支持 Unix 权限 → mount 时必须加 `uid=`, `gid=`, `dmask=`, `fmask=` 选项
- exfat 不支持文件锁（advisory lock）→ SQLite 在 exfat 上多进程写入有风险
- `sudo modprobe exfat` 确保内核模块已加载
- exfat 的 256K 分配单元导致 ls/find/du 在数据量大时极慢
- Docker 容器内 `127.0.0.1` 指向容器自身，不是宿主机 → 代理配置需用 `--network host` 或宿主机网关 IP
- 如需换 ext4 解决兼容性问题，参考 `references/exfat-to-ext4-conversion.md`

### Docker `--restart always` 行为
- `docker stop name` → 容器停止不会自动重启（Docker 标记为手动停止）
- `docker kill name` → 容器停止会自动重启（视为异常退出）
- 系统重启 → 自动拉起（无论之前是 stop 还是 kill）
- 容器被 `docker rm` 删除后数据还在挂载盘 → 只需重新 `docker run` 相同挂载参数即可恢复

### HuggingFace 模型缓存与 exfat
详见 `references/docker-exfat-migration.md`。关键点：huggingface_hub 在 exfat 上自动回退到复制文件而非 symlink，可用 `HF_HUB_DISABLE_SYMLINKS_WARNING=1` 抑制警告。旧的 symlink 缓存需彻底删除后重新下载。

### fstab 最佳实践
- **永远使用 UUID** 而非设备名（如 `/dev/sda1`）
- 编辑后运行 `sudo findmnt --verify` 检查语法
- 运行 `sudo systemctl daemon-reload` 刷新 systemd 缓存

### ⚠️ ext4 挂载参数陷阱（从 exfat 迁移时的常见错误）

**症状：** 系统启动后备份盘未挂载，`docker info` 报错或 symlink 指向的目录不可用。

**诊断：**
```bash
journalctl -b 0 -p err | grep -i "ext4\|mount\|unknown"
# 典型错误: ext4: Unknown parameter 'uid'
```

**原因：** ext4 文件系统**不支持** `uid=`, `gid=`, `dmask=`, `fmask=` 这些挂载选项（它们是 vfat/exfat/ntfs 专用的）。如果 fstab 中给 ext4 分区加了这些参数，内核会直接拒绝整条挂载项：

```
# ❌ 错误 — ext4 用了 exfat 参数，整行无效
UUID=xxx /mnt/backup ext4 defaults,uid=1000,gid=1000,dmask=022,fmask=133 0 0

# ✅ 正确 — ext4 原生支持 UNIX 权限，无需这些参数
UUID=xxx /mnt/backup ext4 defaults 0 0
```

**触发场景：** 备份盘从 exfat 格式化为 ext4 后，fstab 未同步更新。

**修复：**
1. 从 fstab 中删除 uid/gid/dmask/fmask 参数
2. `sudo findmnt --verify` 检查语法
3. `sudo systemctl daemon-reload` 刷新 systemd
4. `sudo mount /mnt/backup` 挂载验证

**注意：** ext4 原生存储 UNIX 所有者/权限，挂载后需要用 `chown -R user:group /mountpoint` 设置所有权，**而非挂载时传入 uid/gid**。

### 文件编码
- 中文文件名在 ZIP 中可能用 GBK 编码 → 用 `unzip -O gbk` 解压

### ⚠️ 假 `.gz` 文件导致 `BadGzipFile` 崩溃

**场景**: 遍历日志目录时，`list_input_files` 扫到文件名以 `.gz` 结尾的文件，调用 `gzip.open()` 时报 `BadGzipFile: Not a gzipped file (b'[2')`。

**根因**: 有人将 `.txt` 日志文件重命名为 `.gz`（或直接保存为 `.gz` 后缀但内容未压缩），导致文件扩展名与内容不匹配。

**排查**:
```bash
file suspicious.gz       # 输出 "ASCII text" 而非 "gzip compressed data"
head -c 4 suspicious.gz  # 正常的 gzip 以 \\x1f\\x8b 开头，假的是文本开头
```

**修复选项**:
1. 代码中增加容错：在 `iter_lines_from()` 的 gzip 分支捕获 `BadGzipFile`，回退到普通文本读取
2. 扫描时跳过 `.gz` 文件或只处理 `.txt` 文件
3. 手动修正：`mv fake.gz fake.txt`

**预防**: `list_input_files()` 用文件魔数（magic bytes）而非扩展名判断压缩格式，或者在扫描目录时先 `file` 命令检查。

---
## 💬 用户交互式清理工作流

当用户要求"清理垃圾"时，不要直接执行清理命令。按以下流程操作：

### 第 1 步：展示磁盘概览（用户喜欢的格式）

```bash
# 总览
df -hT | grep -v tmpfs | grep -v overlay | grep -v devtmpfs

# 系统盘各目录
du -sh ~/* ~/.* 2>/dev/null | sort -rh | head -30

# 各类缓存详细
du -sh ~/.cache/* 2>/dev/null | sort -rh | head -15
journalctl --disk-usage 2>/dev/null
du -sh ~/.local/share/Trash/ 2>/dev/null
```

用户偏好**表格 + 视觉进度条**格式展示，如：
```
┌─────┬──────┬────────┬────────┬──────┐
│ 挂载点 │ 类型 │ 总大小 │ 已用    │ 占比  │
├─────┼──────┼────────┼────────┼──────┤
│ /   │ ext4 │ 227G   │ 48G    │ 23%  │
└─────┴──────┴────────┴────────┴──────┘
系统盘: 48G/227G ■■■■■■■░░░░░░░░░░░░░ 23%
```

### 第 2 步：分类列出可清理项

| 类别 | 项目 | 典型大小 | 需要sudo? |
|------|------|---------|----------|
| 安全 | 缩略图缓存 ~/.cache/thumbnails/ | ~8M | 否 |
| 安全 | pip 缓存 ~/.cache/pip/ | ~1M | 否 |
| 安全 | Hermes 旧日志 ~/.hermes/logs/*.1/.2 | ~20M | 否 |
| 安全 | Hermes 粘贴历史 ~/.hermes/pastes/ | ~5M | 否 |
| 安全 | 回收站 ~/.local/share/Trash/ | 可变 | 部分(Docker volumes需要) |
| 需sudo | journalctl 日志 | 可变 | 是 |
| 需sudo | Snap 旧版本 | 500M-1G | 是 |
| 需sudo | APT 缓存 | ~5M | 是 |

**该用户偏好"只清安全的"** — 只清理不需要 sudo 的项目，Docker volume 文件留到用户有空时 sudo 处理。

### 第 3 步：提供给用户选择

用 clarify 工具提供选项：
1. 全清（含 sudo 项）
2. 只清安全的
3. 自定义选择
4. 跳过

### 第 4 步：执行并验证

```bash
# 安全清理
rm -rf ~/.cache/thumbnails/*
rm -rf ~/.local/share/Trash/files/* ~/.local/share/Trash/expunged/* 2>/dev/null
rm -f ~/.hermes/logs/*.1 ~/.hermes/logs/*.2 ~/.hermes/logs/*.log.*
rm -f ~/.hermes/pastes/*.txt
rm -rf ~/.cache/pip/*

# 验证清理结果
du -sh ~/.cache/thumbnails/ ~/.local/share/Trash/ ~/.hermes/logs/ ~/.hermes/pastes/ ~/.cache/pip/ 2>/dev/null
```

**注意：** Hermes 运行时日志文件会重新生成，清除的是旧版本备份（*.1, *.2, *.log.*）。

---

## 📋 快速命令参考

### Snap 清理（释放系统盘）

```bash
snap list --all | grep "已禁用" | while read n v r t; do
  sudo snap remove "$n" --revision="$r"
done
```

### 系统日志清理

```bash
sudo journalctl --vacuum-size=200M
sudo apt clean
```

详见 `references/disk-management.md`。

---

## 🖥️ 远程 LLM 推理部署

当用户需要在另一台 Windows/Linux 机器上部署本地 LLM 推理机，与当前 Ubuntu 上的 Hermes Agent 配合使用时：

### 推荐架构

```
Ubuntu 24 (Hermes 控制端)           Win11 (推理机)
┌────────────────────┐   局域网    ┌──────────────────────┐
│ Hermes Agent       │  HTTP API  │ WSL2 + llama.cpp     │
│ custom_providers   │←──────────→│ + ROCm/CUDA           │
│ 指向推理机 IP:端口  │            │ + GGUF 模型仓库       │
└────────────────────┘            └──────────────────────┘
```

### 关键步骤

1. **推理机准备**: WSL2 (Linux 环境) + ROCm (AMD GPU) 或 CUDA (NVIDIA GPU)
2. **推理引擎**: llama.cpp 编译带 GPU 支持 (`-DGGML_HIP=ON` 或 `-DGGML_CUDA=ON`)
3. **模型选择**: GGUF Q4_K_M 量化, 7B~16B 参数, 约 4~9GB
4. **服务暴露**: `llama-server --host 0.0.0.0 --port 8080` (监听所有网卡)
5. **端口转发** (WSL2 NAT 模式): `netsh interface portproxy add v4tov4`
6. **Hermes 配置**: `custom_providers.gem12.api_base = http://<推理机IP>:8080/v1`
7. **脱网运行**: 直连网线 + 本地模型 + 本地知识库, 无需互联网

### 性能参考 (8845HS RDNA3)

| 模型 | 量化 | 速度 | 内存 |
|------|------|------|------|
| DeepSeek-Coder-V2-Lite 16B | Q4_K_M | 12-18 tok/s | ~15GB |
| Qwen2.5-14B | Q4_K_M | 12-20 tok/s | ~14GB |
| Qwen2.5-7B | Q4_K_M | 20-35 tok/s | ~9GB |

### 注意事项
- WSL2 使用 NAT 模式时需 Windows 端口转发才能被局域网访问
- 务必设置 `--host 0.0.0.0` 而非默认的 `127.0.0.1`
- Windows Defender 防火墙需放行推理端口 (8080/8081)
- 双模型可以同时启动 (不同端口), Hermes 配置多个 provider 按需切换
- 完整 SOP 见知识库: `~/knowledge/ops/hermes-win11-remote-llm-sop.md`

---

## 参考文件

- `references/disk-management.md` — 磁盘发现、挂载、fstab、清理、目录分析
- `references/system-disk-optimization.md` — 系统盘空间分析与优化（分类清理 + 批量 symlink 迁移到外置盘）
- `references/backup-strategies.md` — rsync 备份、cron 定时、exfat 陷阱、备份验证
- `references/docker-exfat-migration.md` — Docker 容器数据迁移到 exfat 备份盘的完整流程（含 HuggingFace 模型缓存处理、代理配置、已知坑点）
- `references/desktop-install.md` — SoapUI、shell 安装器控制台模式、BitRock/install4j 安装器处理

## 相关技能

- [[cron-job-ops]] — cron job 调度和排障
- [[hardware-diagnostics]] — 硬件健康检查
- [[ubuntu24-ops]] — Ubuntu 24.04 专项运维（PCIe AER 修复等）
