# Hermes Agent China Cloud Deploy

中国大陆云服务器（腾讯云/阿里云/华为云等）部署 Hermes Agent 的完整流程。核心挑战：GitHub 被墙、PyPI 镜像可行、腾讯云安全码 SSH 认证。

## 典型场景

| 场景 | 方法 | 原因 |
|------|------|------|
| GitHub 不可达 | PyPI 镜像 pip install | GnuTLS recv error (-110) |
| SSH 慢（每次显示 QR 码） | ControlMaster 持久连接 | 腾讯云安全模式 |
| 需要同步本地技能 | rsync（每次几 MB） | 本地有完整技能库 |
| 需要同步配置 | rsync config.yaml + .env | 文件小（~24K） |

## 步骤

### 1. SSH 持久连接（腾讯云专用）

腾讯云每次 SSH 都会显示微信扫码安全码横幅（~3s 延迟）。用 ControlMaster 避免每命令重复认证：

```bash
# ~/.ssh/config
Host tencent
  HostName <ip>
  User andymao
  IdentityFile ~/.ssh/tencent-cloud.pem
  ControlMaster auto
  ControlPath ~/.ssh/controlmasters/%r@%h:%p
  ControlPersist 30m

mkdir -p ~/.ssh/controlmasters
ssh -Nf tencent  # 一次认证，后续命令复用
```

### 2. 安装 Hermes Agent（PyPI 镜像）

**不要**用官方安装脚本或 git clone（GitHub 不可达）。用清华 PyPI 镜像：

```bash
ssh tencent '
export PATH="$HOME/.hermes/bin:$PATH"
cd ~/.hermes

# uv 创建 venv（如果已安装 uv）
uv venv venv --python 3.11

# 从清华镜像安装 hermes-agent
source venv/bin/activate
uv pip install hermes-agent --index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 建立 hermes 命令软链接
ln -sf ~/.hermes/venv/bin/hermes ~/.local/bin/hermes
'
```

验证：
```bash
ssh tencent '~/.local/bin/hermes --version'
# 输出: Hermes Agent v0.16.0 ...
```

### 3. 同步技能

首次：完整 rsync（~150MB，22MB 压缩传输）
后续：增量 rsync（仅差异文件）

```bash
rsync -avz --delete ~/.hermes/skills/ tencent:~/.hermes/skills/
```

注意 `--delete` 参数——确保腾讯云删除本地已移除的技能。

### 4. 同步配置

```bash
rsync -avz ~/.hermes/config.yaml tencent:~/.hermes/config.yaml
rsync -avz ~/.hermes/.env tencent:~/.hermes/.env
```

### 5. 同步插件

```bash
rsync -avz ~/.hermes/plugins/ tencent:~/.hermes/plugins/
```

### 6. 最终验证

```bash
ssh tencent '
export PATH="$HOME/.local/bin:$PATH"
echo "=== 版本 ===" && hermes --version
echo "=== 技能数 ===" && ls ~/.hermes/skills/ | wc -l
echo "=== 配置 ===" && hermes config show | head -5
'
```

## 避坑指南

### GitHub Clone 必然失败

在中国大陆云服务器上，GitHub HTTPS 直连会报：
```
fatal: unable to access 'https://github.com/...': GnuTLS recv error (-110)
```

**不要**尝试以下方法（已验证无效）：
- ❌ `git config --global http.proxy http://127.0.0.1:7897` — 本机代理在本地，不在云服务器上
- ❌ `curl -s --proxy http://127.0.0.1:7897` — 同样 `127.0.0.1` 是云服务器自身

**正确方案**：走 PyPI 镜像（清华、阿里云、中科大），或从本地 rsync 整个 repo。

### 大文件传输时间

- 2.2G hermes-agent 源码库 → rsync/tar 管道会超时（`~/.hermes/hermes-agent/` 含 .git history）
- 解决方案：不传源码，只 pip install + 传技能/配置（~22MB 压缩）
- 如果必须传源码：排除 .git/objects/pack/ 用 `rsync --exclude='.git/objects/'`

### 腾讯云安全码

- 每次 SSH 都会显示 QR 码横幅，但不影响命令执行
- ControlMaster 可大幅减少重复认证
- `ssh -Nf` 后台维持连接后，后续命令不再需要扫码

### 服务自启动

腾讯云服务器重启后 Hermes 不会自动启动。如需自启动：
- systemd user service（需要 `loginctl enable-linger`）
- crontab `@reboot` 方式
- 腾讯云自动化助手（TencentCloud Automation Tools）

## 快速命令（完整流程）

```bash
# 1. SSH ControlMaster
ssh -Nf tencent

# 2. 安装 Hermes
ssh tencent 'cd ~/.hermes && uv venv venv --python 3.11 && source venv/bin/activate && uv pip install hermes-agent --index-url https://pypi.tuna.tsinghua.edu.cn/simple && ln -sf ~/.hermes/venv/bin/hermes ~/.local/bin/hermes'

# 3. 同步技能+配置+插件
rsync -avz --delete ~/.hermes/skills/ tencent:~/.hermes/skills/
rsync -avz ~/.hermes/config.yaml tencent:~/.hermes/config.yaml
rsync -avz ~/.hermes/.env tencent:~/.hermes/.env
rsync -avz ~/.hermes/plugins/ tencent:~/.hermes/plugins/

# 4. 验证
ssh tencent '~/.local/bin/hermes --version && echo "Skills: $(ls ~/.hermes/skills/ | wc -l)"'
```
