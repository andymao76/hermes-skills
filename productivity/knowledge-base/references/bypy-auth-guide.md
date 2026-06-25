# bypy 百度网盘授权指南

bypy (Baidu Yun Python client) 通过百度 OAuth 2.0 授权访问用户网盘。

## 首次授权步骤

```bash
pip3 install --user --break-system-packages bypy
python3 -m bypy info
```

输出会显示类似：
```
Please visit:
https://openapi.baidu.com/oauth/2.0/authorize?client_id=q8WE4EpCsau1oS0MplgMKNBn&response_type=code&redirect_uri=oob&scope=basic+netdisk
And authorize this app
Paste the Authorization Code here within 10 minutes.
Press [Enter] when you are done
```

需要**手动完成**（Hermes 终端是 CLI，没有浏览器）：
1. 在有浏览器的设备上打开上面的 URL
2. 登录百度账号
3. 授权后得到 Authorization Code
4. 回到终端粘贴授权码并回车

**重要陷阱**：授权码**不能用管道输入**（`echo "code" | python3 -m bypy info` 会超时），PTY 模式下的交互输入也会超时。必须在普通终端前台直接粘贴。

## 授权文件

授权成功后，token 保存在 `~/.bypy/bypy.json`（bypy 不同版本位置有差异，也可能是 `~/.bypy.json`），包含 access_token 和 refresh_token 的 JSON 文件。

后续使用 bypy 不再需要重新授权，除非删除此文件或 token 过期。

## 部分授权导致的陷阱

如果 `bypy info` 授权流程被中断（Ctrl+C、超时等），token 文件可能**已部分写入**。
此时再次运行 `python3 -m bypy info` 仍然要求授权，但旧 token 可能已可用——

**建议的诊断方法**：
```bash
# 先直接测试是否已授权
python3 -m bypy list

# 如果仍有内容输出，说明已授权成功
# 如果 token 已写入但 bypy 不认，可以删掉重新执行完整授权流程
rm -f ~/.bypy/bypy.json ~/.bypy.json
```

## 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| `EOFError: EOF when reading a line` | bypy 在非交互式终端运行时没有 stdin 输入 | 不要用 nohup/background，在前台交互运行 |
| `Maximum number (1) of tries failed` | 被 GFW 墙了，授权服务器连不上 | 设置代理环境变量 `HTTPS_PROXY=127.0.0.1:7897`（如有）再试 |
| `token expired` | access_token 过期 | bypy 会自动用 refresh_token 刷新，如果刷新失败需重新授权 |

## 操作目录

bypy 只能访问百度网盘中的 `/apps/bypy/` 目录。
- 要下载的文件需要先手动移到该目录下（在百度网盘网页/客户端操作）
- 或者用 ln 软链方式（不推荐）

## 常用命令

```bash
python3 -m bypy list                              # 列出 /apps/bypy/ 根目录
python3 -m bypy list path/to/subdir              # 列出子目录
python3 -m bypy downdir / ~/baidupan_docs/       # 下载整个目录到本地
python3 -m bypy upload localfile.txt              # 上传文件到网盘
python3 -m bypy compare                           # 比较本地和云端差异
python3 -m bypy quota                             # 查看网盘容量
```

## 速度说明

免费用户 API 下载速度约 80~200 KB/s，这是百度网盘官方 API 的限制，bypy 本身不加速。

大批量文件（5GB+）建议：
- 分多次下载，避免超时
- 用 `--processes 4` 启用多线程下载（bypy v1.8.9 支持）
- 考虑 BaiduPCS-Go (qjfoidnh 分支) 代替，下载速度更快
