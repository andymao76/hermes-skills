# Obsidian 远程访问 via Samba

> 原则：**Windows 不留副本，所有文件在 Ubuntu**，Samba 只读共享。

## 安装与配置

```bash
# Ubuntu 端
sudo apt install -y samba
sudo smbpasswd -a andymao        # 设置访问密码
sudo cp /tmp/smb.conf /etc/samba/smb.conf
sudo systemctl restart smbd && sudo systemctl enable smbd
```

## Samba 配置

```ini
[obsidian]
   comment = Obsidian Vault (read-only via network)
   path = /home/andymao/Documents/Obsidian Vault
   browseable = yes
   read only = yes
   valid users = andymao
   force user = andymao
```

## Windows 连接

1. 打开 `此电脑` → 右键 `映射网络驱动器`
2. 文件夹: `\\192.168.1.53\obsidian`
3. 勾选 `使用其他凭据连接`
4. 用户名 `andymao` / 密码（smbpasswd 设置的）
5. Obsidian 中打开此路径作为仓库

## 关键

- `.obsidianignore` 中排除 `knowledge/`（852MB），否则 Windows 加载极慢
- 知识库通过 `知识/` symlink 按需访问，不自动索引
- 防火墙: `sudo ufw allow samba`
