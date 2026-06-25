# Dify Web 3000 端口与 Open WebUI 无冲突

## 现象

用户观察到 Open WebUI 和 Dify Web 都使用 3000 端口，怀疑端口冲突。

## 真相

**没有冲突。** Dify Web 容器的 3000 端口**没有映射到宿主机**：

```bash
docker port docker-web-1
# 返回空 — 未映射到宿主机的任何端口
```

Dify Web 仅在 Docker 内部网络 `docker_default` 中监听 3000，通过 Nginx 反向代理访问：

```
用户 → http://localhost/ (宿主机 80)
     → Nginx (容器 :80)
     → proxy_pass http://web:3000 (Docker 内部 DNS)
```

而 Open WebUI 的 3000 是直接绑定在宿主机 0.0.0.0:3000：

```
ss -tlnp | grep ":3000 "
# users:("open-webui",pid=...,fd=29)
```

两者完全隔离。

## 验证方式

```bash
# 检查任意端口是否有宿主机映射
docker port docker-web-1

# 对比访问路径
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/   # Open WebUI
curl -sL -o /dev/null -w "%{http_code}" http://localhost/        # Dify (经 Nginx 80)
```

## 教训

看到两个服务都用 3000 端口时不要假设冲突。Docker 容器的内部端口和宿主机端口是独立的网络空间。「都叫 3000」在 Docker 语境下可能是：
- 容器 1 的 3000 映射到宿主机 3000（冲突）
- 容器 1 的 3000 未映射（内部使用），容器 2 的 3000 映射到宿主机（无冲突）
- 两者都未映射（都通过反向代理访问，无冲突）

始终用 `docker port <container>` 验证后再下结论。
