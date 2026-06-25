# ztlig.cfg VNEID ↔ 实际网元名提取方法

## 适用场景

当需要在本地分析 ztlig.cfg 配置中 VNEID（虚拟网元 ID）与物理网元的映射关系时使用。适用于 A1 项目多运营商（SU/ZAIN/MTN）多站点（PSD/ATB/KHS/KTN）的 ZTLIG 配置分析。

## 前置条件

- 本地有 ztlig.cfg 文件备份（A1 项目在 `~/projects/A1/202606/A1-ZTLIG-CONFIG/` 和 `~/work-projects/A1/cfg/`）
- 配置文件命名规则：`{运营商}-{站点}-{域}-ztlig.cfg`
  - 运营商: SU(苏丹电信/Sudatel), ZAIN, MTN
  - 站点: A(PSD苏丹港/主站), B(ATB阿特巴拉/远程站)
  - 域: CS(电路域), PS(分组域)

## 核心 awk 提取脚本

### 1. 快速列出所有 VNEID 映射

```bash
awk -F'[=;]' '
  /^ztlig\.vne\./ {
    split($1, a, ".")
    idx = a[3]; key = a[4]; gsub(/^ +| +$/, "", key)
    val = $2; gsub(/^ +| +$/, ";", val); gsub(/;+$/, "", val); gsub(/^ +| +$/, "", val)
    v[idx,key] = val
  }
  END {
    for (k in v) {
      split(k, b, SUBSEP)
      if (b[2] == "vneid")
        printf "VNEID=%-3s  tneid=%-3s  hi2_neid=%-15s  operid=%-5s  type=%-4s\n",
          v[b[1],"vneid"], v[b[1],"tneid"], v[b[1],"hi2_neid"], v[b[1],"operid"], v[b[1],"vne_type"]
    }
  }
' ztlig.cfg | sort -t= -k2 -n
```

### 2. 完整映射（含华为 alias）

华为网元（hw_cs/hw_epc）使用 `hw.alias` 字段存储网元名。需同时解析 `ztlig.ne` 和 `ztlig.vne` 块进行交叉引用：

```bash
awk -F'[=;]' '
  /^ztlig\.vne\./ {
    split($1, a, ".")
    idx = a[3]; key = a[4]; gsub(/^ +| +$/, "", key)
    val = $2; gsub(/^ +| +$|;+$/, "", val)
    v[idx,key] = val
  }
  /^ztlig\.ne\./ {
    split($1, a, ".")
    idx = a[3]; key = a[4]; gsub(/^ +| +$/, "", key)
    val = $2; gsub(/^ +| +$|;+$/, "", val); gsub(/^ +| +$/, "", val)
    n[idx,key] = val
  }
  END {
    for (k in v) {
      split(k, b, SUBSEP)
      if (b[2] == "vneid") {
        tn = v[b[1],"tneid"]
        al = n[tn,"alias"] ? n[tn,"alias"] : "-"
        vn = n[tn,"vendor"] ? n[tn,"vendor"] : "-"
        ve = n[tn,"version"] ? n[tn,"version"] : "-"
        ip = n[tn,"x1_ip"] ? n[tn,"x1_ip"] : "-"
        vt = v[b[1],"vne_type"] ? v[b[1],"vne_type"] : "-"
        printf "VNEID=%-2s  %-25s  %-6s/%-10s  %-15s  type=%-4s  op=%-5s\n",
          v[b[1],"vneid"], al, vn, ve, ip, vt, v[b[1],"operid"]
      }
    }
  }
' ztlig.cfg | sort -t= -k2 -n
```

### 3. 按 valid_fg 筛选有效/无效网元

```bash
grep "valid_fg" ztlig.cfg
grep "valid_fg" ztlig.cfg | grep "=1"  # 仅有效
```

### 4. 批量处理多个配置文件

```bash
for f in ~/projects/A1/202606/A1-ZTLIG-CONFIG/*.cfg; do
  echo "=== $(basename $f) ==="
  awk -F'[=;]' '/^ztlig\.vne\./{
    split($1,a,"."); idx=a[3]; key=a[4]; gsub(/^ +| +$/,"",key)
    val=$2; gsub(/^ +| +$|;+$/,"",val); v[idx,key]=val
  }/^ztlig\.ne\./{
    split($1,a,"."); idx=a[3]; key=a[4]; gsub(/^ +| +$/,"",key)
    val=$2; gsub(/^ +| +$|;+$/,"",val); n[idx,key]=val
  }END{
    for(k in v){
      split(k,b,SUBSEP)
      if(b[2]=="vneid"){
        tn=v[b[1],"tneid"]; al=n[tn,"alias"]?n[tn,"alias"]:"-"
        vn=n[tn,"vendor"]?n[tn,"vendor"]:"-"
        printf "  VNEID=%-2s → %-25s [%s]\n", v[b[1],"vneid"], al, vn
      }
    }
  }' "$f" | sort -t= -k2 -n
  echo
done
```

## 输出解读

### VNE 类型编码

| vne_type | 含义 | incptType | speechtype | 典型用途 |
|----------|------|-----------|------------|---------|
| MSCs | CS 域 MSCe/MSC Server | 3(IRI+CC) | 0(合并) | 传统语音呼叫 |
| IMS | IMS 域网元(OMU/CSCF/ATS) | 1(仅IRI) | 1(分离) | VoLTE/VoWiFi SIP 信令 |
| SBC | 会话边界控制器 | 3(IRI+CC) | 1(分离) | 接入/互联边界控制 |
| MME | PS 域 移动管理实体 | — | — | EPC 信令 |
| SGW | PS 域 服务网关 | — | — | EPC 用户面 |

### 运营商 operid 对照

| operid | 运营商 | MCC |
|--------|--------|-----|
| 63407 | SU (Sudatel) | 634 |
| 63401 | ZAIN Sudan | 634 |
| 63402 | MTN Sudan | 634 |

### 已知 VNEID 分段

| 范围 | 运营商 | 站点/域 | 典型网元 |
|------|--------|---------|---------|
| 1~6 | SU | PSD-CS | mAGCF,GMSC,OMU-ATS-CSC,I-SBC,VOBBATS,A-SBC |
| 7~9 | MTN | 两站-CS | ZTE 网元 |
| 10~14 | ZAIN | PSD-CS | mAGCF,GMSC,OMU,ISBC,ASBC |
| 17~18 | SU | PSD-CS | IMGW01,IMGW02 |
| 19~20 | SU/ZAIN | PSD-PS | USN01(MME),CGW01(SGW) |
| 23~32 | SU | KHS-CS | mAGCF,GMSC,OMU,VOBBATS,I-SBC,A-SBC |
| 25~29 | ZAIN | KTN-CS | mAGCF,GMSC,OMU,ISBC,ASBC |
| 35~36 | MTN | 两站-CS | ZTE 网元 |
| 41~42 | ZAIN | KTN-PS | USN01(MME),CGW01(SGW) |

## 常见注意事项

1. **华为 vs ZTE alias 差异**：华为网元用 `ztlig.ne.x.hw.alias` 存储网元名；ZTE 网元无此字段（用 `ztslig.vne.x.ztev4lis.alias` 替代）
2. **valid_fg=0** 表示该网元已被禁用（如 SU 的 KHS-VOBBATS VNEID=31），查询 `hts_lig_hi2` 时不会出现这些 VNEID
3. **同一运营商 A/B 站配置几乎相同**：仅 LIG IP、leaid、x1_user 不同，VNEID 映射结构一致
4. **incptType 决定上报类型**：3=IRI+CC 都上报（CS域/SBC），1=仅 IRI（IMS域）
5. 完整映射表见 `~/knowledge/li/OWLS/A1项目ztlig.cfg-VNEID映射表.md`
