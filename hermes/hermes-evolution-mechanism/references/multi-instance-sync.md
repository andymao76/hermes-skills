# MCP 统一工作流 & 内容同步限制

## MCP 统一（两边互补）

当本地和远程使用不同的 MCP 服务集合时，最佳实践是**合并两边**：

### 分析差异

```bash
# 获取两边 MCP 配置
grep -A3 '^\s\s\s\s\S\+:' ~/.hermes/config.yaml | grep -B1 'command:' | grep -E '^\s\s\s\s\S\+:|^\s\s\s\s\s\scommand:' 

# 远程
ssh tencent "sudo grep -A3 '^\s\s\s\s\S\+:' /home/ubuntu/.hermes/config.yaml"
```

### 常见互补组合

| 本地常有 | 远程常有 |
|----------|---------|
| 中国平台 MCP：csdn, jd, taobao, xiaohongshu, zhihu, wikipedia | 基础工具：filesystem, obsidian, time, chart, web-search(duckduckgo) |
| github-gov1 (wrapper 版本) | github (npm 版本) |
| db-query | sqlite |

### 本地补充远程特有的 MCP

```bash
npm install -g @modelcontextprotocol/server-filesystem
npm install -g obsidian-mcp-server
pip install mcp-server-time
pip install chart-mcp
```
然后添加到 config.yaml 的 mcp_servers 段，reload 生效。

### 远程补充本地特有的 MCP

远程可能需要：
- 从本地拷贝自定义 MCP 脚本（csdn、jd、taobao、zhihu 等）
- 安装对应依赖（Python 包、Node 包）
- 配置 GitHub CLI (gh) 和 wrapper 脚本
- 调整路径（远程路径为 /home/ubuntu/...）

## 内容同步限制规则

部分内容 **不可同步到远程服务器**，仅限本地：

| 类别 | 路径/技能 | 说明 |
|------|----------|------|
| LI 协议文档 | knowledge/hi2/ | 华为 LI 协议标准（CS/5GC/X1/X2/X3/ASN1） |
| LI 运维文档 | knowledge/li/ | ZTLIG 运维手册、A1 项目、国际项目含 LI |
| OWLS | knowledge/research/OWLS_* | OWLS 系统架构、三码补全、虚实碰撞 |
| LI skill | huawei-hi2 | 华为 HI2 接口 |
| LI skill | zte-li | 中兴 LI 协议 |
| LI skill | playwright-cli-openclaw | Web 自动化（归入 LI 范畴） |

> 同步前必须用 `--exclude` 或手动筛选排除上述内容。

## 本地 → 远程同步（MEMORY + RULE V5.1）

### 架构定义

| 层 | 内容 | 路径 |
|----|------|------|
| 🧠 MEMORY | 用户偏好 + 用户画像 | `~/.hermes/memories/{MEMORY.md,USER.md}` |
| 💡 RULE (Skills) | Hermes 可执行工作流 | `~/.hermes/skills/` |
| 💡 RULE (Knowledge) | 知识库（陈述记忆） | `~/knowledge/` |

### 前置条件

```bash
# SSH 连接（腾讯云）
Host tencent
  HostName 124.222.206.209
  User andymao
  IdentityFile ~/.ssh/tencent-cloud.pem
  ControlMaster auto
  ControlPath ~/.ssh/controlmasters/%r@%h:%p
  ControlPersist 30m
```

### 同步步骤

#### 1. 同步 MEMORY

```bash
scp ~/.hermes/memories/MEMORY.md ~/.hermes/memories/USER.md tencent:~/.hermes/memories/
```

#### 2. 同步 RULE - Skills

```bash
rsync -av ~/.hermes/skills/ tencent:~/.hermes/skills/
```

#### 3. 同步 RULE - Knowledge（核心大数据量同步）

```bash
rsync -av --progress --delete \
  --exclude='li/' \
  --exclude='hi2/' \
  --exclude='secrets/' \
  --exclude='OWLS_*' \
  --exclude='articles_baidu/' \
  --exclude='ima-sync/' \
  ~/knowledge/ tencent:~/knowledge/
```

- `--delete` 保证远程结构与本地一致
- 排除项覆盖 LI/OWLS/密钥等保护内容

#### 4. 验证

```bash
ssh tencent 'cat ~/.hermes/memories/MEMORY.md | head -3'
ssh tencent 'ls ~/.hermes/skills/ | wc -l'
ssh tencent 'du -sh ~/knowledge/'
```

### 注意事项

- `config.yaml` **各自独立维护**，不做自动 merge
- 远程可能未安装 `hermes` CLI pip 包，同步仍是文件级
- 首次同步 ~900MB，通常 2-3 分钟；增量同步秒级
- SSH ControlMaster 存活检查：`ssh -O check tencent`

## 配置同步规则

两边的 config.yaml 各自独立维护，核心区别：

| 方面 | 远程(腾讯云) | 本地 |
|------|-------------|------|
| 主模型 | deepseek-v4-flash | deepseek-v4-flash |
| Provider | 7 个（同本地） | 7 个 |
| 平台 | 待确认 | feishu + discord + whatsapp + telegram |
| MCP 生态 | 基础工具 | 中国平台 |

不建议自动 merge 配置。
