# Utimaco LIMS RAI v16.1 — 快捷参考

## 目标管理命令一览

| 命令 | 关键参数 | 输出 |
|------|---------|------|
| tadd | icd(M), tno(M), ttype(M), net(M), dtype(M), doo(M), mc_voice(C), mc_iri(C), mc_data(C), flags/area/NEID/LBS | tno_created tno_id=N |
| tlist | icd(O), tno(O) | 完整目标配置 + tno_id |
| tdel | tno_id(M), doo(M) | 无输出 |
| tmod | tno_id(M), doo(M), 其余均为 O（不传保留, 传入替换） | 无输出 |
| tstate | icd(M), tno(M), doo(M) — 均为 M | 无输出 |
| tnelist | neid(M) — 逗号分隔 NE ID | netarget neid= tno= |

## tmod 关键语义

- 使用 tno_id（Integer）而非 tno+ttype
- doo 唯一必填 M；所有 mc_xxx/NEID/LBS/flags 均为 O
- mc_xxx: 不传保留，传入必须是已存在 MC ID 并替换
- liid="": 清空 LI 标识
- net/dtype: 逗号分隔列表
- net/dtype/mc_xxx 非独立，需遵循业务规则

## MC 管理命令一览

| 命令 | 关键参数 | 输出 | 特殊点 |
|------|---------|------|--------|
| mclist | mc(O), lea(O) | 38 字段（含 Genband C20 参数） | 261/262/340/341 |
| mcadd | lea(M), mctype(M), 其余按类型 C | mc_created mc=MCId | 按 MC 类型参数集差异大 |
| mcdel | mc(M) | 无输出 | 被目标引用时 630 |
| mcmod | mc(M), 其余 O | 无输出 | 各 MC 类型允许不同参数集 |

## NE 管理命令一览

| 命令 | 关键参数 | 输出 | 状态码 |
|------|---------|------|--------|
| nelist | neid(O), provider(O), all(O) | ne neid= netype= ... ttype= | 700-749 |
| neadd | neid(M), netype(M), osversion(M), param1-paramx(M) | ne_created neid=NeId | 700-749, 900 |
| nedel | neid(M) | 无输出 | 700-749 |

## tnelist 特殊属性
- 非确定性实现：两次相同参数结果可能不同
- 仅部分供应商 NE 支持（Nokia, Huawei, Broadsoft, Starent, Sonus, Ericsson 等）
- 仅审计员可用
- Parsing Error 是 Communication Error 子类型，应通过 NE 配置修复
