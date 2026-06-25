# Dify 上游仓库维护案例

## 背景

仓库: `langgenius/dify` (克隆到 `~/dify/`)

## 发现的问题

`git status` 显示 6 个未跟踪文件:

```
?? docker/diagnose.sh
?? docker/dify-diagnose.sh
?? docker/dify_logs_20260603_094140.txt
?? docker/manage.sh
?? docker/quick_diagnose.sh
?? docker/view_logs.sh
```

- 5 个 shell 脚本 (共 283 行) — 用户自写的诊断/管理工具
- 1 个日志文件 (835KB) — 一次性诊断输出，不应入版本控制

## 处理步骤

### 1. 分类

| 文件 | 类型 | 处理方式 |
|------|------|---------|
| `diagnose.sh` (58行) | 诊断脚本 | 移到 `~/scripts/dify/` |
| `dify-diagnose.sh` (95行) | 深度诊断 | 移到 `~/scripts/dify/` |
| `manage.sh` (45行) | 服务管理 | 移到 `~/scripts/dify/` |
| `quick_diagnose.sh` (39行) | 快速诊断 | 移到 `~/scripts/dify/` |
| `view_logs.sh` (46行) | 日志查看 | 移到 `~/scripts/dify/` |
| `dify_logs_*.txt` (835KB) | 临时日志 | 直接删除 |

### 2. 执行

```bash
mkdir -p ~/scripts/dify
mv ~/dify/docker/diagnose.sh ~/scripts/dify/
mv ~/dify/docker/dify-diagnose.sh ~/scripts/dify/
mv ~/dify/docker/manage.sh ~/scripts/dify/
mv ~/dify/docker/quick_diagnose.sh ~/scripts/dify/
mv ~/dify/docker/view_logs.sh ~/scripts/dify/
rm ~/dify/docker/dify_logs_20260603_094140.txt
```

### 3. .gitignore 更新

```bash
# 追加具体文件名而非通配
echo "" >> ~/dify/.gitignore
echo "# User-added diagnostic scripts (moved to ~/scripts/dify/)" >> ~/dify/.gitignore
echo "docker/diagnose.sh" >> ~/dify/.gitignore
echo "docker/dify-diagnose.sh" >> ~/dify/.gitignore
echo "docker/manage.sh" >> ~/dify/.gitignore
echo "docker/quick_diagnose.sh" >> ~/dify/.gitignore
echo "docker/view_logs.sh" >> ~/dify/.gitignore
echo "docker/*.txt" >> ~/dify/.gitignore
```

### 4. 验证

```bash
cd ~/dify && git status --short
# 结果:  M .gitignore   ✅ 只有 .gitignore 有修改
```

## 后续

- 脚本统一在 `~/scripts/dify/` 中，可直接执行
- Dify 启动: `cd ~/dify/docker && docker compose up -d`
- 端口: HTTP 80, HTTPS 443
- IP: `192.168.1.49` (局域网固定 IP)
