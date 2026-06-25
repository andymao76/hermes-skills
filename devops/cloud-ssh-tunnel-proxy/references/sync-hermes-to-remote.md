# 同步 Hermes 配置到远程服务器

当本地和远程（如腾讯云）各运行一个 Hermes 实例时，需要同步三个组件：

## 需要同步的内容

| 组件 | 位置 | 同步频率 |
|------|------|----------|
| **技能 (skills/)** | `~/.hermes/skills/` | 按需（新增技能后） |
| **API Keys (.env)** | `~/.hermes/.env` | 每次新增/修改 key 后 |
| **记忆 (memory)** | `~/.hermes/memory/` | 按需（sqlite 数据库，不常用） |

## 技能同步

```bash
# 1. 本地打包
cd ~/.hermes && tar czf /tmp/hermes-skills.tar.gz skills/

# 2. SCP 到远程临时目录
scp /tmp/hermes-skills.tar.gz tencent:/tmp/

# 3. 远程解压到目标目录（注意用户归属）
ssh tencent "sudo tar xzf /tmp/hermes-skills.tar.gz -C /home/ubuntu/.hermes/ && \
  sudo chown -R ubuntu:ubuntu /home/ubuntu/.hermes/skills/"

# 4. 验证
ssh tencent "sudo find /home/ubuntu/.hermes/skills/ -name 'SKILL.md' | wc -l"
```

### 要点
- 远程 Hermes 可能属于不同系统用户（如 `ubuntu`），需 `sudo` 写入
- 解压后必须 `chown` 修正权限，否则 Hermes 无法读取
- `tar czf` 压缩后约 29MB（原 96MB 的 skills 目录）

## API Key 同步

```bash
# 直接 SCP .env 到远程临时目录，再 sudo 复制
scp ~/.hermes/.env tencent:/tmp/hermes-env
ssh tencent "sudo cp /tmp/hermes-env /home/ubuntu/.hermes/.env && \
  sudo chown ubuntu:ubuntu /home/ubuntu/.hermes/.env && \
  sudo chmod 600 /home/ubuntu/.hermes/.env"
```

### 要点
- `.env` 包含明文 API Key，必须 `chmod 600`（仅属主可读）
- 远程 `.env` 可能已有不同的 key（如远程特有的平台 Token），直接覆盖前先备份
- 同步后通过 `rh "测试"` 验证远端 API 调用正常

## 注意事项

- **权限问题**：本地用户（`andymao`）通过 SSH 登录远程后是不同用户（`andymao` vs `ubuntu`），无法直接读 `/home/ubuntu/` 目录。所有远程操作需要 `sudo`。
- **`HOME` 环境变量**：SSH 登录后 `$HOME` 默认指向本地用户名（`/home/andymao`），远程 Hermes 需要改为 `/home/ubuntu`，否则 `.git` 权限错误。
- **不推荐同步记忆 (memory/)**：SQLite 数据库含路径信息，可能绑定本地目录结构。远程 Hermes 的记忆应独立建立。
- **同步前备份远程现有配置**：先 `ssh tencent "sudo tar czf /tmp/hermes-backup-$(date +%Y%m%d).tar.gz -C /home/ubuntu/.hermes skills/ .env"`。
