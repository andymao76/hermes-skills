#!/usr/bin/env bash
# ASN.1 编解码辅助脚本使用说明
# 在 skill 中引用: skill_view("asn1-codec", "scripts/use-asn1-codec.sh")

PYTHON=~/.hermes/venv/bin/python
SCRIPT=~/.hermes/scripts/asn1-codec.py

echo "ASN.1 编解码工具 — 快速参考"
echo "================================"
echo ""
echo "BER 编码整数 255:"
$PYTHON $SCRIPT encode-int 255
echo ""
echo "BER 编码布尔 TRUE:"
$PYTHON $SCRIPT encode-bool True
echo ""
echo "BER 解码 02012a (INTEGER 42):"
$PYTHON $SCRIPT decode-hex 02012a
echo ""
echo "BER 解码 0101ff (BOOLEAN TRUE):"
$PYTHON $SCRIPT decode-hex 0101ff
echo ""
echo "工具版本信息:"
$PYTHON $SCRIPT info
