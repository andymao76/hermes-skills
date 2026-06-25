# 案例：中兴 ZTE LIG 配置文件中文乱码

## 问题描述

ZTE LIG 设备配置文件 `A-su-cs-ztlig.cfg` 中中文注释显示为 ã€�æŽ¥å�£ 等乱码。

## 根因

非中文 Windows 环境下的 MobaXterm 打开该文件后，通过复制/粘贴重新生成保存，导致原始 UTF-8 中文在剪贴板链路中被错误转码。

## 诊断输出

```
enca A-su-cs-ztlig.cfg           → UTF-8
file -i A-su-cs-ztlig.cfg        → charset=utf-8
iconv -f UTF-8 -t UTF-8 ...      → 无报错
locale                           → zh_CN.UTF-8
echo "中文测试"                    → 正常
nl -ba A-su-cs-ztlig.cfg | head  → 显示 æŽ¥å�£ 等
```

## 修复

重新通过 SFTP 下载原始 .cfg 文件，不再使用终端复制粘贴。
