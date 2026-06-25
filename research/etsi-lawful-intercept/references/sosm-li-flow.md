# SOSM 系统 — 主叫用户触发监听及 X3 通道建立流程

## 来源
文件: `/home/andymao/LI/SOSM/S001 SOSM_主叫用户触发监听以及X3通道建立流程.vsd` (Visio)
转换方式: LibreOffice (.vsd → PDF) → pdftotext → Markdown
知识库: `~/knowledge/research/SOSM_主叫触发监听_X3通道建立流程.md`

## 涉及实体

| 缩写 | 全称 | 角色 |
|------|------|------|
| CCB | Call Control Block | 呼叫控制 |
| MGRA | Media Gateway Resource Agent | 媒体网关资源 |
| LICI | Lawful Interception Control Interface | 监听控制接口 |
| SOSM | — | 核心调度/监听管理 |
| IGW | Interception Gateway | 拦截网关 |
| CDBI | Call Data Base Interface | 呼叫数据库接口 |
| BCLIB | Bearer Control Library | 承载控制库 |

## 信令流程概要

```
User→CCB: SETUP(带监听标志)
CCB→MGRA: 申请MASTER T1+T2承载
CCB→LICI: LICI_start_x3_call (触发X3通道建立)
LICI→SOSM: 申请SLAVE T1+T2(2次)
SOSM→CDBI: DB_ASSIGN_CTL / EN_LICI_CR_CALLINIT
SOSM→MONITOR/TG: SETUP → DB_QUERY_TERMINATION_BY_BSN
BCLIB: 中继网关ADD成功
LICI→MGRA: MOD S1/S2 → SEND ONLY (只收不发)
LICI→SOSM: EN_LICI_CR_ACTIVE → SCS_ACTIVE
SOSM→被叫: 发起SETUP
```

## 与华为 LI 文档的对应关系

- X3 通道建立 → 华为文档中的 X3 接口 (NE↔DF3 通信内容复制)
- LICI/SOSM/IGW → LIG (ADMF/DF2/DF3) 架构
- SEND ONLY → 华为文档 speechType (语音分离模式)
