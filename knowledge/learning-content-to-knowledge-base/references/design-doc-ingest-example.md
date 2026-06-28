# 设计文档入库示例：STCS V2.0 HTTP2 子模块

此文件记录 2026-06-28 会话中的设计文档入库实例，供未来 agent 参考。

## 来源文档

- **文档类型**：详细设计说明书（V1.0）
- **内容来源**：用户直接粘贴完整文档内容到聊天
- **文档结构**：封面 → 修改记录 → 目录 → 编写目的 → 术语定义 → 模块描述 → 模块设计 → 数据结构 → 接口说明 → 函数定义 → 特殊说明 → 参考资料

## 输入信号

- 文档以「技术文件名称： STCS V2.0 HTTP2子模块详细设计」封面行开头
- 包含完整目录（第一章~第九章）
- 包含 `typedef struct` C 结构体定义
- 包含状态机枚举定义
- 用户指令：「学习并归纳到STCS项目里」

## 处理步骤

1. **文档类型识别** → 详细设计文档
2. **分层提取**：
   - 元数据：STCS V2.0, ASPF 模块, HTTP2 子模块
   - 架构：LM → HTTP2 → SBI
   - 数据结构：h2_context_t, h2_stream_t, h2_frame_info_t, h2_fix_hdr_t 等
   - 设计决策：不支持动态 HPACK 字典、二级跨包状态机、3s stream 老化
   - 接口：h2_dissect_protocol, h2_dissect_process, http2_init, http2_expire_protocol
3. **去噪**：丢弃 mxGraphModel base64/urlencode 的 SVG 图形数据
4. **入库**：`knowledge/01_PROJECTS/STCS/stcs-v2-http2-submodule-design.md`
5. **索引更新**：`enzyme refresh`

## 入库格式要点

- 分类目录：`01_PROJECTS/STCS/`（项目级，非通用 telecom/）
- 结构体用代码块保留原始 C 定义，下方接 Markdown 字段说明表
- 设计决策用两栏对比表呈现（决策项 → 选择 → 原因）
- 帧类型处理策略用量表（帧类型 → 处理策略）
- 返回值速查表（宏名 → 值 → 含义）

## 可复用技巧

- 设计文档中的 `%3CmxGraphModel%3E` 等 URL 编码数据是 draw.io SVG 中间格式，直接丢弃
- C struct 中 `H2_PACKED` 等宏是厂商自定义，在注释中标注忽略
- 状态机枚举（一级/二级）用缩进层级模拟迁移关系
- 多值宏定义（如 8 种 headline type）用场景化表格呈现
