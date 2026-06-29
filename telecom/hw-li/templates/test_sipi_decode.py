#!/usr/bin/env python3
"""
SIP-I (SIP with Encapsulated ISUP) PCAP 解码测试
=================================================
测试流程：
  1. 用 scapy 构造 SIP INVITE + ISUP IAM 二进制负载，写入临时 PCAP
  2. 用 scapy 读回 PCAP，提取 SIP body 中的 ISUP 二进制负载
  3. 解码 ISUP 各字段（消息类型、CIC、Called/Calling Party Number）
  4. pytest 断言验证

依赖：scapy, pytest（无需 tshark/pyshark）

ISUP 参考：
  - ITU-T Q.763 (ISUP 格式规范)
  - ITU-T Q.764 (ISUP 信令流程)
  - RFC 3372 (SIP-T)

使用方式：
  pytest test_sipi_decode.py -v
"""

import struct
import base64
import tempfile
import os
import pytest
from scapy.all import Ether, IP, UDP, Raw, wrpcap, rdpcap


# ============================================================
# Helper：构造 ISUP IAM 二进制负载
# ============================================================

def build_isup_iam_binary(
    called_number: str = "8613800138000",
    calling_number: str = "8613900213900",
    cic: int = 123,
    opc: int = 0x060504,
    dpc: int = 0x030201,
    sls: int = 0x0A,
) -> bytes:
    """
    构造 ISUP IAM (Initial Address Message) 二进制负载。

    ISUP IAM 结构 (Q.763):
      [路由标签] [CIC] [消息类型] [必选固定参数] [必选可变参数] [可选参数]

    路由标签 (4 bytes):
      byte 0-1: DPC (Point Code, 大端序)
      byte 2-3: OPC (大端序)
               (实际 SS7 中 DPC/OPC 各 3 bytes, 这里简化)

    参数:
        called_number: 被叫号码字符串
        calling_number: 主叫号码字符串
        cic: Circuit Identification Code
        opc: Originating Point Code
        dpc: Destination Point Code
        sls: Signaling Link Selection
    """
    payload = bytearray()

    # ---- 路由标签 (Routing Label, 4 bytes) ----
    # Q.704: DPC(2) + OPC(2) + SLS(1)
    payload.extend(struct.pack(">H", dpc >> 8))  # DPC high
    payload.extend(struct.pack(">H", opc >> 8))  # OPC high
    payload.append(sls & 0xFF)  # SLS

    # ---- CIC (Circuit Identification Code, 2 bytes, 大端序) ----
    payload.extend(struct.pack(">H", cic & 0xFFFF))

    # ---- 消息类型 (1 byte): 0x01 = IAM ----
    payload.append(0x01)

    # ---- Nature of Connection Indicators (1 byte) ----
    # bit 0-1: satellite indicator (00=none)
    # bit 2-3: continuity check (00=not required)
    # bit 4: echo control device (0=not included)
    payload.append(0x00)

    # ---- Forward Call Indicators (2 bytes) ----
    # 0x0000 = 国内呼叫，非端到端方式
    payload.extend(b"\x00\x00")

    # ---- Called Party Number (必选可变参数) ----
    # 被叫号码编码：
    #   Nature of Address (1 byte) + 地址信号 (BCD, 反序 nibble)
    #   奇数位数补 'F'
    payload.append(0x04)  # Tag: Called Party Number
    bcd_called = _number_to_bcd(called_number)
    payload.append(len(bcd_called) + 1)  # Length: NOA(1) + BCD digits
    payload.append(0x80)  # Nature of Address: 国内号码
    payload.extend(bcd_called)

    # ---- Calling Party Number (可选可变参数) ----
    payload.append(0x0A)  # Tag: Calling Party Number
    bcd_calling = _number_to_bcd(calling_number)
    payload.append(len(bcd_calling) + 2)  # Length: NOA(1) + NAI(1) + BCD digits
    payload.append(0x80)  # Nature of Address: 国内号码
    payload.append(0x03)  # Numbering Plan Indicator: ISDN
    payload.extend(bcd_calling)

    return bytes(payload)


def _number_to_bcd(number_str: str) -> bytes:
    """电话号码转 BCD 编码（反序 nibble，奇数位补 F）"""
    digits = number_str.replace("+", "")
    if len(digits) % 2 == 1:
        digits += "F"  # 奇数位补 F
    bcd = bytearray()
    for i in range(0, len(digits), 2):
        high = int(digits[i + 1], 16)
        low = int(digits[i], 16)
        bcd.append((high << 4) | low)
    return bytes(bcd)


# ============================================================
# Helper：构造 SIP-I 数据包
# ============================================================

def build_sipi_packet(
    call_id: str = "test-sipi-call-001@test.local",
    from_uri: str = "sip:8613900213900@test.local",
    to_uri: str = "sip:8613800138000@test.local",
    isup_payload: bytes = None,
) -> bytes:
    """
    构造包含 SIP-I ISUP body 的完整 SIP 数据包（Ether/IP/UDP/SIP 层）。

    返回 scapy Ether 层的字节表示。
    """
    if isup_payload is None:
        isup_payload = build_isup_iam_binary()

    b64_isup = base64.b64encode(isup_payload).decode()

    from_tag = "fromtag001"
    to_uri_short = to_uri.replace("sip:", "")
    from_uri_short = from_uri.replace("sip:", "")

    body_parts = [
        f"--boundary001",
        "Content-Type: application/sdp",
        "",
        "v=0",
        "c=IN IP4 192.168.1.100",
        "m=audio 10000 RTP/AVP 0",
        f"--boundary001",
        "Content-Type: application/isup; version=itu-t94+",
        "Content-Disposition: session; handling=required",
        "",
        b64_isup,
        "--boundary001--",
        "",
    ]
    body_str = "\r\n".join(body_parts)
    content_length = len(body_str.encode("utf-8"))

    sip_headers = "\r\n".join([
        f"INVITE {to_uri} SIP/2.0",
        "Via: SIP/2.0/UDP 192.168.1.100:5060;branch=z9hG4bK-test",
        "Max-Forwards: 70",
        f"From: <{from_uri}>;tag={from_tag}",
        f"To: <{to_uri}>",
        f"Call-ID: {call_id}",
        "CSeq: 1 INVITE",
        f"Contact: <{from_uri}>",
        "Content-Type: multipart/mixed;bound=boundary001",
        f"Content-Length: {content_length}",
    ])

    sip_message = sip_headers + "\r\n\r\n" + body_str

    # 构造以太网包
    packet = (
        Ether()
        / IP(src="192.168.1.100", dst="10.0.0.2")
        / UDP(sport=5060, dport=5060)
        / Raw(load=sip_message.encode("utf-8"))
    )
    return bytes(packet)


# ============================================================
# Helper：从 PCAP 提取 ISUP body
# ============================================================

def extract_sip_body_from_pcap(pcap_path: str) -> list[dict]:
    """用 scapy 读取 PCAP，提取 SIP 消息中的 body 内容。"""
    results = []
    packets = rdpcap(pcap_path)

    for i, pkt in enumerate(packets):
        if Raw in pkt and UDP in pkt and pkt[UDP].dport == 5060:
            raw_load = pkt[Raw].load
            if isinstance(raw_load, bytes):
                raw_text = raw_load.decode("utf-8", errors="replace")
            else:
                raw_text = str(raw_load)

            lines = raw_text.split("\r\n")

            # 第一遍：提取 SIP 头
            headers = {}
            body_lines = []
            in_body = False
            for line in lines:
                if in_body:
                    body_lines.append(line)
                elif ": " in line:
                    key, val = line.split(": ", 1)
                    headers[key.lower()] = val
                elif line == "":
                    in_body = True

            call_id = headers.get("call-id", "unknown")

            # 第二遍：从 body_lines 中提取 ISUP base64
            isup_decoded = None
            in_isup_section = False
            mime_headers_done = False
            b64_buffer = ""

            for bline in body_lines:
                # 结束 boundary: --boundary001--
                if bline.startswith("--") and bline.endswith("--") and len(bline) > 4:
                    if in_isup_section and b64_buffer.strip():
                        try:
                            isup_decoded = base64.b64decode(b64_buffer.strip())
                        except Exception:
                            pass
                    break

                # 新 MIME section 开始: --boundary001
                if bline.startswith("--") and not bline.endswith("--"):
                    in_isup_section = False
                    mime_headers_done = False
                    b64_buffer = ""
                    continue

                # 匹配 ISUP section
                if "application/isup" in bline:
                    in_isup_section = True
                    mime_headers_done = False
                    b64_buffer = ""
                    continue

                # 在 ISUP section 中：跳过 MIME headers，收集 base64 body
                if in_isup_section:
                    if not mime_headers_done:
                        if bline == "":
                            mime_headers_done = True
                    else:
                        b64_buffer += bline

            results.append({
                "index": i,
                "call_id": call_id,
                "isup_data": isup_decoded,
                "headers": headers,
            })
    return results


# ============================================================
# Helper：解码 ISUP IAM 字段
# ============================================================

def decode_isup_iam(payload: bytes) -> dict:
    """
    从 ISUP IAM 二进制负载中提取关键字段。

    返回 dict: message_type, cic, opc, dpc, called_party_number, calling_party_number
    """
    info = {}

    if payload is None or len(payload) < 12:
        info["error"] = "payload too short"
        return info

    pos = 0

    # 路由标签 (4 bytes): DPC(2) + OPC(2) + SLS(1)
    dpc_raw = struct.unpack(">H", payload[pos:pos+2])[0]
    pos += 2
    opc_raw = struct.unpack(">H", payload[pos:pos+2])[0]
    pos += 2
    sls = payload[pos]
    pos += 1

    info["dpc"] = f"{(dpc_raw >> 8) & 0xFF}.{(dpc_raw >> 4) & 0x0F}.{dpc_raw & 0x0F}"
    info["opc"] = f"{(opc_raw >> 8) & 0xFF}.{(opc_raw >> 4) & 0x0F}.{opc_raw & 0x0F}"
    info["sls"] = sls

    # CIC (2 bytes)
    info["cic"] = struct.unpack(">H", payload[pos:pos+2])[0]
    pos += 2

    # 消息类型 (1 byte)
    msg_type = payload[pos]
    pos += 1

    msg_types = {
        0x01: "IAM", 0x02: "IAI", 0x03: "SAM", 0x04: "INR",
        0x05: "INF", 0x06: "ACM", 0x07: "CON", 0x08: "LPA",
        0x09: "ANM", 0x0A: "SUS", 0x0B: "RES", 0x0C: "REL",
        0x0D: "RLC", 0x0E: "RSC", 0x0F: "BLG", 0x10: "BLA",
        0x11: "UBL", 0x12: "UBA", 0x13: "CCR", 0x14: "RSP",
        0x15: "CGB", 0x16: "CGU", 0x17: "GRA", 0x18: "CQM",
        0x19: "GRS", 0x1A: "CVR", 0x1B: "CVS", 0x1C: "PAM",
        0x1D: "FOT", 0x1E: "UPT", 0x1F: "DRG",
    }
    info["message_type_code"] = msg_type
    info["message_type"] = msg_types.get(msg_type, f"Unknown(0x{msg_type:02X})")

    # 跳过必选固定参数: Nature of Connection(1) + Forward Call Indicators(2)
    pos += 3

    # 解析 TLV 参数
    while pos < len(payload):
        tag = payload[pos]
        pos += 1
        if pos >= len(payload):
            break
        length = payload[pos]
        pos += 1
        if pos + length > len(payload):
            break
        value = payload[pos:pos+length]
        pos += length

        if tag == 0x04:  # Called Party Number
            if len(value) >= 1:
                noa = value[0]
                bcd_digits = value[1:]
                info["called_party_number"] = _bcd_to_number(bcd_digits)
                info["called_party_noa"] = noa
        elif tag == 0x0A:  # Calling Party Number
            if len(value) >= 2:
                noa = value[0]
                npi = value[1]
                bcd_digits = value[2:]
                info["calling_party_number"] = _bcd_to_number(bcd_digits)
                info["calling_party_noa"] = noa
                info["calling_party_npi"] = npi

    return info


def _bcd_to_number(bcd_data: bytes) -> str:
    """BCD 编码转回电话号码字符串"""
    digits = []
    for byte in bcd_data:
        low = byte & 0x0F
        high = (byte >> 4) & 0x0F
        if high != 0x0F:  # F = filler
            digits.append(str(high))
        if low != 0x0F:
            digits.append(str(low))
    return "".join(digits)


# ============================================================
# 测试用例
# ============================================================

class TestSIPIDecode:
    """SIP-I PCAP 解码完整流程测试"""

    @pytest.fixture
    def sample_pcap_path(self):
        """Fixture: 创建包含 SIP-I 包的临时 PCAP 文件"""
        isup_payload = build_isup_iam_binary(
            called_number="8613800138000",
            calling_number="8613900213900",
            cic=123,
        )
        pkt_bytes = build_sipi_packet(
            call_id="test-sipi-call-001@test.local",
            isup_payload=isup_payload,
        )
        pkt = Ether(pkt_bytes)

        fd, path = tempfile.mkstemp(suffix=".pcap")
        os.close(fd)
        wrpcap(path, pkt)
        yield path
        os.unlink(path)

    # ---- 基本功能测试 ----

    def test_sip_callid_extraction(self, sample_pcap_path):
        """验证 SIP Call-ID 提取"""
        results = extract_sip_body_from_pcap(sample_pcap_path)
        assert results[0]["call_id"] == "test-sipi-call-001@test.local", \
            f"Call-ID 不匹配: {results[0]['call_id']}"

    def test_isup_raw_extraction(self, sample_pcap_path):
        """验证从 SIP body 中提取到 ISUP 原始二进制负载"""
        results = extract_sip_body_from_pcap(sample_pcap_path)
        assert results[0]["isup_data"] is not None, "未提取到 ISUP body"
        assert len(results[0]["isup_data"]) > 10, "ISUP body 太短"

    def test_isup_message_type_iam(self, sample_pcap_path):
        """验证 ISUP 消息类型为 IAM (0x01)"""
        results = extract_sip_body_from_pcap(sample_pcap_path)
        isup_data = results[0]["isup_data"]
        decoded = decode_isup_iam(isup_data)
        assert decoded.get("message_type_code") == 0x01, \
            f"消息类型不是 IAM: {decoded.get('message_type_code')}"

    def test_isup_called_party_number(self, sample_pcap_path):
        """验证 Called Party Number 解码正确"""
        results = extract_sip_body_from_pcap(sample_pcap_path)
        isup_data = results[0]["isup_data"]
        decoded = decode_isup_iam(isup_data)
        assert decoded.get("called_party_number") == "8613800138000", \
            f"Called Party Number 不匹配: {decoded.get('called_party_number')}"

    def test_isup_calling_party_number(self, sample_pcap_path):
        """验证 Calling Party Number 解码正确"""
        results = extract_sip_body_from_pcap(sample_pcap_path)
        isup_data = results[0]["isup_data"]
        decoded = decode_isup_iam(isup_data)
        assert decoded.get("calling_party_number") == "8613900213900", \
            f"Calling Party Number 不匹配: {decoded.get('calling_party_number')}"

    def test_isup_cic_value(self, sample_pcap_path):
        """验证 CIC (Circuit Identification Code) 值"""
        results = extract_sip_body_from_pcap(sample_pcap_path)
        isup_data = results[0]["isup_data"]
        decoded = decode_isup_iam(isup_data)
        assert decoded.get("cic") == 123, \
            f"CIC 不匹配: {decoded.get('cic')}"

    # ---- 集成测试 ----

    def test_full_decode_pipeline(self, sample_pcap_path):
        """
        完整解码管道测试：
        构造 → 写入 PCAP → 读取 PCAP → 提取 ISUP → 解码 → 验证所有字段
        """
        results = extract_sip_body_from_pcap(sample_pcap_path)
        assert len(results) == 1, f"期望 1 个包，实际 {len(results)}"

        r = results[0]
        decoded = decode_isup_iam(r["isup_data"])

        # 打印完整解码结果
        print(f"\n  ┌─ SIP-I Decode Pipeline ──────────────────────────")
        print(f"  │ Call-ID:            {r['call_id']}")
        print(f"  │ ISUP Message Type:  {decoded['message_type']}")
        print(f"  │ CIC:                {decoded['cic']}")
        print(f"  │ OPC:                {decoded['opc']}")
        print(f"  │ DPC:                {decoded['dpc']}")
        print(f"  │ Called Party Nbr:   {decoded['called_party_number']}")
        print(f"  │ Calling Party Nbr:  {decoded['calling_party_number']}")
        print(f"  └──────────────────────────────────────────────────")

        assert r["call_id"] == "test-sipi-call-001@test.local"
        assert decoded["message_type_code"] == 0x01
        assert decoded["cic"] == 123
        assert decoded["called_party_number"] == "8613800138000"
        assert decoded["calling_party_number"] == "8613900213900"

    def test_multiple_packets(self):
        """
        测试多个 SIP-I 包在同一个 PCAP 中的场景。
        模拟 3 个不同呼叫。
        """
        calls = [
            ("call-001", "8613800138000", "8613900213900"),
            ("call-002", "8613900123456", "8613800654321"),
            ("call-003", "8613711112222", "8613722223333"),
        ]

        packets = []
        for call_id, called, calling in calls:
            isup = build_isup_iam_binary(
                called_number=called, calling_number=calling
            )
            pkt_bytes = build_sipi_packet(
                call_id=call_id, isup_payload=isup
            )
            packets.append(Ether(pkt_bytes))

        fd, path = tempfile.mkstemp(suffix=".pcap")
        os.close(fd)
        wrpcap(path, packets)

        try:
            results = extract_sip_body_from_pcap(path)
            assert len(results) == 3, f"期望 3 个包，实际 {len(results)}"

            for i, (call_id, called, calling) in enumerate(calls):
                r = results[i]
                decoded = decode_isup_iam(r["isup_data"])
                assert r["call_id"] == call_id, f"#{i} Call-ID 不匹配"
                assert decoded["called_party_number"] == called, f"#{i} Called 不匹配"
                assert decoded["calling_party_number"] == calling, f"#{i} Calling 不匹配"
        finally:
            os.unlink(path)
