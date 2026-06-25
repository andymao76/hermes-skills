# Samba 网络共享配置

## 服务端（Ubuntu）

```bash
sudo apt install samba
sudo smbpasswd -a andymao   # 设置 SMB 密码（可不同于系统密码）
sudo cp /tmp/smb.conf /etc/samba/smb.conf
sudo systemctl restart smbd && sudo systemctl enable smbd
sudo ufw allow samba
```

## Samba 配置（`/etc/samba/smb.conf`）

```ini
[obsidian]
   comment = Obsidian Vault (read-only)
   path = /home/andymao/Documents/Obsidian Vault
   browseable = yes
   read only = yes
   valid users = andymao
   force user = andymao
```

## 客户端（Windows）

1. 此电脑 → 映射网络驱动器
2. 文件夹: `\\192.168.1.53\obsidian`
3. 用户名: `andymao`，密码: smbpasswd 设置的密码
4. Obsidian 中打开 Z 盘作为仓库

## 注意

- 只读共享，Windows 不留副本
- `knowledge/` symlink 在 Windows 上不可用（已通过 `.obsidianignore` 排除）
- 首次加载稍慢（网络枚举），之后秒级
