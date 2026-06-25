# 百度网盘文档导入与分类指南

## RULE⑪ 规则

百度网盘下载的文档（`baidu-netdisk/`、`articles_baidu/`）需经安全审计分类后使用。

## 分类标准

下载文件后，按以下规则判断归属：

| 文件内容特征 | 目标目录 | 示例 |
|-------------|---------|------|
| LI 相关内容（合法监听、HI、X1-X2-X3、ZTLIG、OWLS 等） | `knowledge/li/baidu-netdisk-import/` | `合法监听.md`, `LI-HW.pdf` |
| 客户项目文档（商务、合同、客户名） | `knowledge/customers/` | 工勘表、投标书 |
| 密码、Token、密钥 | `knowledge/secrets/` | 密码本、证书文件 |
| 公开技术文档（3GPP、ETSI、RFC、通用技术） | 留在 `baidu-netdisk/` 或迁至对应 LEVEL 1 目录 | 核心网、5G、IMS 等 |

## 已迁移内容

以下 LI 内容已从 `baidu-netdisk/` 迁移到 `li/baidu-netdisk-import/`：

| 源路径 | 目标路径 | 文件 |
|--------|---------|------|
| `baidu-netdisk/合法监听.md` | `li/baidu-netdisk-import/` | LI 文档索引（85 份文档） |
| `baidu-netdisk/files/LI-HW.pdf` | `li/baidu-netdisk-import/files/` | 华为 LI 实现指南 |
| `baidu-netdisk/files/HW_NGN_X1X2.pdf` | `li/baidu-netdisk-import/files/` | 华为 NGN X1/X2 接口文档 |
| `baidu-netdisk/parsed/LI-HW.md` | `li/baidu-netdisk-import/parsed/` | 解析后的 LI-HW 文档 |
| `baidu-netdisk/parsed/HW_NGN_X1X2.md` | `li/baidu-netdisk-import/parsed/` | 解析后的 X1X2 文档 |
| `articles_baidu/合法监听LI/` | `li/baidu-netdisk-import/articles_baidu/` | 爱立信/Airtel TMC 等 5 份文档 |

## 操作流程

```bash
# 1. 检查网盘下载的文件中是否含 LI/项目内容
grep -rl 'LIID\|IMSI\|合法监听\|ZTLIG\|OWLS\|X1_X2' ~/knowledge/baidu-netdisk/parsed/*.md

# 2. 确认后迁移
mkdir -p ~/knowledge/li/baidu-netdisk-import/{files,parsed}
cp ~/knowledge/baidu-netdisk/合法监听.md ~/knowledge/li/baidu-netdisk-import/
cp ~/knowledge/baidu-netdisk/files/LI-* ~/knowledge/li/baidu-netdisk-import/files/

# 3. 重建语义索引
cd ~/knowledge && ~/.hermes/scripts/enzyme-init.sh
```

## 安全注意事项

- 百度网盘可能包含混合内容（一个下载包里有公开技术+LI 文档），需逐文件分类
- 分类完成前，该文件视为 LEVEL 5，**不得**进入 RAG 索引
- 迁移后用 `security-audit.py` 验证：`baidu-netdisk/` 目录不应再被标记为敏感
