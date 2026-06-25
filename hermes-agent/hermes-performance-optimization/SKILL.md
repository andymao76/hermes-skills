---
name: hermes-performance-optimization
description: Hermes Agent 性能优化技能 — 解决响应慢、上下文压缩频繁、工具加载过多等问题
trigger: 用户提到性能慢、卡顿、优化、响应慢、工具加载慢等关键词时自动加载
---

# Hermes Agent 性能优化技能

来源: `~/andymao_Doc/Hermes Agent 性能优化技能.docx`（Andy 环境专用）
适用: Ubuntu 24.04 + Hermes 0.16+

## 一、快速诊断

```bash
hermes doctor               # 全面检查
hermes --version            # 查看版本
hermes update               # 检查更新
hermes doctor --fix         # 自动修复
```

## 二、模型优化

| 场景 | 推荐模型 |
|------|----------|
| 日常问答/CLI交互 | `deepseek-v4-flash` / `qwen/qwen3.6-flash` / `qwen/qwen3.7-plus` |
| 深度分析/复杂项目 | `deepseek-v4-pro` / `claude-opus` / `gpt-5.5` |

```bash
hermes chat -m deepseek-v4-flash
```

## 三、上下文压缩优化

**信号**: 出现 "Preflight compression" / "Compacting context" / "Session compressed"

**方案**:
- 每个项目单独开会话，不要一个会话用几天
- 定期 `hermes session list` + `hermes session delete <id>` 清理历史
- 会话超过 5+ 次交互建议 `/new`

## 四、工具集精简

| 场景 | 命令 |
|------|------|
| 运维 | `hermes chat -t terminal,file` |
| 运维+搜索 | `hermes chat -t terminal,file,web` |
| 开发 | `hermes chat -t terminal,file,web,code_execution` |
| 普通问答 | `hermes chat -t web` |

## 五、代理配置

```bash
export HTTP_PROXY=http://127.0.0.1:7897
export HTTPS_PROXY=http://127.0.0.1:7897
export NO_PROXY=localhost,127.0.0.1,::1
```

永久生效写入 `~/.bashrc`

## 六、Gateway 优化

```bash
hermes gateway install      # 安装为系统服务
hermes gateway start        # 后台常驻
hermes gateway status       # 查看状态
```

避免每次启动重复加载 Gateway。

## 七、系统依赖

```bash
# 基础
sudo apt install -y git ripgrep fd-find jq curl unzip build-essential python3-pip python3-venv nodejs npm
# Browser 工具
sudo apt install -y xvfb xdotool x11-utils scrot imagemagick fonts-noto-cjk
```

## 八、性能监控

```bash
htop      # CPU
free -h   # 内存
df -h     # 磁盘
uptime    # 负载
```

## 九、启动模板

| 模式 | 命令 |
|------|------|
| 运维 | `hermes chat -t terminal,file -m deepseek-v4-flash` |
| 搜索 | `hermes chat -t terminal,file,web -m deepseek-v4-flash` |
| 研发 | `hermes chat -t terminal,file,web,code_execution -m deepseek-v4-pro` |
| 知识库 | `hermes chat -t terminal,file,web,memory -m qwen/qwen3.7-plus` |

## 十、最佳实践

优先级:
1. 使用 Flash 模型
2. 控制会话长度（5+ 交互 /new）
3. 精简工具集
4. 修复代理配置
5. 定期更新 Hermes
6. 启用 Gateway 服务
7. 安装 Browser 依赖
8. 监控资源占用

## Andy 环境默认配置

```yaml
系统: Ubuntu 24.04.4 LTS
Python: 3.12
Hermes: 0.16.x
代理: 127.0.0.1:7897
默认启动: hermes chat -t terminal,file,web -m deepseek-v4-flash
适用: Linux运维, 大数据平台巡检, Kafka/Flink, OpenWebUI, Dify, Neo4j, Obsidian, Hermes开发
```
