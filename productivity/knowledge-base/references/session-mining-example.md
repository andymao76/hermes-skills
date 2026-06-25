# 会话挖掘入库 — 实操案例

> 从本会话中挖掘 Hermes Agent 实战经验存入知识库的完整过程。

## 步骤 1：发现候选会话

```python
session_search(query="部署 OR 配置 OR 修复 OR 排错 OR 架构", limit=10)
session_search(query="Telegram OR Discord OR 微信 OR 集成", limit=10)
session_search(query="Open WebUI OR Bridge OR Dify OR 模型", limit=10)
```

优先选消息数多（>100 条）且标题明确的会话。忽略 auto-title/tag 生成的元数据子会话。

## 步骤 2：滚动浏览关键节点

```python
# 定位到 Bridge 修复的起点
session_search(session_id="20260606_225546_26b394", around_message_id=3299, window=12)

# 滚动查看更多内容
session_search(session_id="20260606_225546_26b394", around_message_id=3335, window=12)
```

## 步骤 3：提炼分类

从 3 场核心会话（832+122+35 消息）提炼出 9 大类内容：

| 类别 | 关键发现 | 来源 |
|------|---------|------|
| systemd 陷阱 | SupplementaryGroups= 空行 → 216/GROUP；patch 工具可能静默失败 | Bridge 修复会话 |
| 代理注入 | systemd user session 不继承 shell 代理变量；需在 Environment 行显式设置 | Gateway 调试会话 |
| Provider 陷阱 | openai provider → openrouter 别名映射；SiliconFlow 国际站需代理 | 模型测试会话 |
| Discord/Telegram | Channel ID vs Server ID；TELEGRAM_ALLOWED_USERS 填人类用户 ID | 平台集成会话 |
| Dify 端口 | Docker 3000 未映射宿主机，与 Open WebUI 不冲突 | 架构审查会话 |

## 步骤 4：写入 + 索引

```bash
# 写入 knowledge/notes/
write_file("knowledge/notes/Hermes Agent 实战运维笔记.md", content)

# 验证可搜索
python3 ~/.hermes/scripts/knowledge/search_knowledge.py "systemd 216 GROUP"
# → 命中：Hermes Agent 实战运维笔记
```

## 研究调研入库案例

除了会话挖掘，knowledge-base 也支持从网上研究→入库的标准流程。两个典型案例：

### IMS SIP 信令流程调研

1. **搜索**：4 组关键词（IMS SIP call flow + Diameter Rx + 中文注册排障 + Q.850 cause codes）
2. **提取**：6 个权威来源（3GPP TS 24.229/24.930、RFC 3261/3665、Cisco、Oracle SBC、Spirent、LinkedIn 专家）
3. **筛选**：排除营销页面、SlideShare 低质内容、CSDN 转载
4. **输出**：22KB .md，10 章含 ASCII 时序图 + 错误码表 + Diameter AVP 速查
5. **验证**：`search_knowledge.py "REGISTER IMS"` / `"Diameter Rx AAR"` / `"QCI"` 均命中

### 2G/3G 呼叫流程调研

1. **搜索**：历史会话中已有 3GPP TS 24.008 原文，额外搜索 GSM/UMTS CC/MM 流程 + Q.850 + CSFB
2. **提取**：7 个来源（TS 24.008 V18.8.0、EventHelix 信令图、YateBTS、RF Wireless World、3GLTEInfo、Qualcomm）
3. **输出**：31KB .md，11 章含 GSM MO/MT 时序图 + Q.850 40+ 编码表 + CSFB 双网回落流程 + 定时器速查

两次调研均遵循「搜索→提取→过滤→结构化→写入→索引→验证」闭环，产物可直接通过 FTS5 检索复现。
