# 远程调用 Hermes CLI（通过 SSH）

当另一台服务器上也部署了 Hermes Agent（gateway 模式），可以从本地通过 SSH 直接调用其 CLI 执行查询。

## 场景

- 腾讯云服务器上运行了 Hermes Gateway
- Hermes 安装路径：`/home/ubuntu/.hermes/`（用户 ubuntu）
- 本地 SSH 配置为不同用户（如 `andymao`）
- 权限：目标文件属于 `ubuntu`，本地 SSH 用户不能直接访问

## 完整调用命令

```bash
ssh tencent "sudo -u ubuntu bash -c 'cd /home/ubuntu && HERMES_HOME=/home/ubuntu/.hermes HOME=/home/ubuntu /home/ubuntu/.hermes/hermes-agent/venv/bin/hermes chat -q '\"'\"'你的问题'\"'\"''"
```

### 拆解说明

| 段 | 作用 |
|---|------|
| `ssh tencent` | 用 SSH config 中配置的 Host 登录 |
| `sudo -u ubuntu bash -c '...'` | 以 ubuntu 用户身份执行 |
| `cd /home/ubuntu` | 进到 ubuntu 的 home 目录（避权限问题） |
| `HERMES_HOME=... HOME=...` | 覆写环境变量，指向 ubuntu 的配置 |
| `hermes chat -q '...'` | 非交互模式执行单次查询 |
| `'\''"'\''\$*'\''"'\''` | SSH 3层嵌套引用的标准转义模式（`'` + `"` + `'` 套嵌） |

## 简化：bash 函数

写入 `~/.bashrc`：

```bash
rh() { ssh tencent "sudo -u ubuntu bash -c 'cd /home/ubuntu && HERMES_HOME=/home/ubuntu/.hermes HOME=/home/ubuntu /home/ubuntu/.hermes/hermes-agent/venv/bin/hermes chat -q '\"'\"'$*'\"'\"''"; }
```

用法：

```bash
rh "服务器运行多久了"
rh "检查 Nginx 配置"
rh "列出 Docker 容器"
```

## 更简单的方式：改 SSH 用户

如果远程服务器的 Hermes 属于同一个 SSH 用户（或可以切换），直接：

```bash
ssh ubuntu@server "/home/ubuntu/.hermes/hermes-agent/venv/bin/hermes chat -q '你好'"
```

## 注意事项

- SSH 命令中 `$` 需要转义或使用单引号 heredoc
- 远程 Hermes 的 venv 路径要确认（`which hermes` 或 `ls ~/.hermes/hermes-agent/venv/bin/`）
- `--accept-hooks` 标志在远程 SSH 调用的非交互模式可能需要额外处理
- 远程 Hermes 如果也开启了 Gateway，两者互不干扰
