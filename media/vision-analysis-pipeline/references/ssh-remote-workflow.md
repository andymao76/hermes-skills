# SSH 远程截图工作流（Windows → Linux）

## 用户的完整工作流

```
Windows 截图 → SCP 传文件 → SSH 终端 → vision_analyze → markitdown → 知识库
```

## SCP 命令

```powershell
# Windows PowerShell / CMD
scp C:\Users\毛恒镇\Pictures\截图.png andymao@服务器IP:/home/andymao/temp-picture/
```

## 缺省目录

- `/home/andymao/temp-picture/` — 截图统一存放点
- 所有 vision_analyze 调用优先从这个目录读图

## 典型场景

| 场景 | 操作 |
|------|------|
| 协议码流截图分析 | SCP 传 HEX/ASN.1 截图 → vision_analyze 理解 → markitdown 存知识库 |
| 技术培训素材 | 截图 → 分析 → markitdown 转 .md → 入库 |
| PPT/PDF 文档 | markitdown 直接转，不经过截图 |

## 注意事项

- 服务器无桌面环境，不可用 `gnome-screenshot` / `scrot`
- 图片传完后直接告诉 Hermes 文件路径即可，不要用 `read_file` 读图片文件
- 如需快速测试连接性，用 `scp -v` 加 verbose 输出
