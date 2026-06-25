# Daily Report Word Template (日报 WORD 文档)

从 `/home/andymao/knowledge/00_INBOX/日报/YYYYMMDD.md` 的内容生成专业 WORD 文档。

## 结构

WORD 文档必须包含以下区段，顺序不可调换：

| 区段 | 内容 | 格式 |
|------|------|------|
| 标题 | 工作日报 + 日期 | 居中大字 |
| 一、今日完成 | 项目 × 工时 × 内容 | 表格（深色表头+斑马纹） |
| 二、日常维护 | 维护事项（必填） | 小标题 + 列表 |
| 三、项目部署 | 部署内容或无（必填） | 段落 |
| 四、关键决策（可选） | 决策 × 原因 | 表格 |
| 五、明日计划 | 待办列表 | 列表 |

## 关键参数

- 字体：Microsoft YaHei（中英文通用）
- 页边距：上下 2.0cm，左右 2.5cm
- 表格样式：Table Grid，深蓝表头 `#0F172A`，斑马纹 `#F1F5F9`
- 文件名：`~/日报_YYYY-MM-DD.docx`

## 平台交付

```bash
# Telegram（通过代理直连）
source ~/.hermes/.env && \
curl -s --max-time 10 --proxy http://127.0.0.1:7897 \
  -F "chat_id=$TELEGRAM_HOME_CHANNEL" \
  -F "document=@/home/andymao/日报_YYYY-MM-DD.docx" \
  -F "caption=📋 工作日报 YYYY-MM-DD（周X）" \
  "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendDocument"

# Discord（需先通过 send_message list 获取 channel ID）
# 微信（iLink 有限流，每次调用间隔至少 30s）
```
