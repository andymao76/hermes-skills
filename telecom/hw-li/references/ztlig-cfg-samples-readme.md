# ztlig.cfg 实际配置样本

以下配置文件是 CS 域真实部署配置，含华为 MSC X1/X2/X3 完整对接参数。
文件位于 `~/projects/A1/` 目录下：

| 文件 | 说明 | 大小 |
|------|------|------|
| B-MTN-CS-ztlig.cfg | 乌干达 MTN CS | 39K |
| B-SU-CS-ztlig.cfg | 苏丹 CS | 89K |
| B-ZAIN-CS-ztlig.cfg | 扎因 CS | 69K |

## 配置内容参考价值
- NE-COM / NE-HW 参数实例 (vendor/version/ip/user/pwd/des_key)
- VNE 映射关系 (vneid ↔ hi2_neid ↔ hw_lioid)
- ZTLIG1/ZTLIG2/ZTLIG3 进程参数
- SSF/RVF 语音还原参数
- LEA Kafka 配置
