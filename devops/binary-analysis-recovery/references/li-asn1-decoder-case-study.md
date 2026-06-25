# LI ASN.1 Decoder — PyInstaller EXE Reverse Engineering Case Study

## Binary Info

| Property | Value |
|----------|-------|
| File | `app_v1_1.exe` (8.9 MB) |
| Type | PyInstaller 2.1+, Python 3.7 |
| Platform | Windows x86-64 GUI |
| Source path | `C:\\Users\\1003787\\Desktop\\wireshark_asn\\asn\\` |

## Extraction

```bash
python3 pyinstxtractor.py app_v1_1.exe
# → /tmp/app_v1_1.exe_extracted/  (111 files)
```

Key files recovered:
- `app_v1_1.pyc` — Main Flask app (371 lines after decompilation)
- `PYZ-00.pyz` → `asn_decode_api.pyc`, `asn_spec.pyc`, `asn_decode_iri_report.pyc`, `mavenir_xml_decode.pyc`

## Key Differences Found Between EXE and Reconstructed Source

### Architecture: Dual-Path vs Unified

The EXE (v1.1) uses a **dual-path architecture** not present in the original v1 source:

```python
# EXE imports two additional decoder functions:
from asn_decode_iri_report import decode_pcap_payload, decode_iri_report, decode_xml_report
from asn_decode_iri_report import decode_ps_iri_report, decode_ps_pcap_payload  # NEW in v1.1

# Two separate dispatch dicts:
pcap_map = {
    "hw_5gc": decode_ps_pcap_payload,   # PS = Packet Switched
    "hw_epc": decode_ps_pcap_payload,
    "zte_epc": decode_ps_pcap_payload,
    # ... existing CS modes via decode_pcap_payload
}
iri_map = {
    "hw_5gc": decode_ps_iri_report,
    "hw_epc": decode_ps_iri_report,
    "zte_epc": decode_ps_iri_report,
    # ... existing CS modes via decode_iri_report
}
```

The v3 reconstruction unified this into a single `decode_hi2_cs_message(data, company)` function that switches on vendor internally.

### Additional Decode Modes in EXE

| Mode | Present in v1 | Present in v1.1 EXE | Present in v3 |
|------|:---:|:---:|:---:|
| hw-cs | ✅ | ✅ | ✅ |
| hw-ims | ✅ | ✅ | ✅ |
| zte-cs | ✅ | ✅ | ✅ |
| g2k | ✅ | ✅ | ✅ |
| utimaco-volte | ✅ | ✅ | ✅ |
| mavenir | ✅ | ✅ | ✅ |
| **hw-5gc** | ❌ | ✅ | ✅ |
| **hw-epc** | ❌ | ✅ | ❌ (no ASN.1 found) |
| **nsn** | ❌ | ✅ | ✅ (as nsn-cs) |
| **zeel-cs** | ❌ | ✅ | ❌ (no ASN.1 found) |
| **zte-epc** | ❌ | ✅ | ✅ |

### ASN.1 Files

| Version | ASN.1 count | Schema count | Source |
|---------|:-----------:|:------------:|--------|
| Original v1 | 20 | 5 | `asnfile/` in project |
| v1.1 EXE | 24 | 7+ | Packed inside EXE, also in `~/LI/software/asn/asnfile/` |
| v3 | 24 | 9 | Same 24 + 4 new from EXE's `asn/` dir |

The 4 new ASN.1 files (in `~/LI/software/asn/asnfile/`):
- `hw_5gc_x2.asn` — Huawei 5GC X2 interface (1197 lines, IRI-Parameters module)
- `hw_sae_x2.asn` — Huawei SAE/LTE X2 interface
- `nsn_cs.asn` — Nokia Siemens CS (OlcmReport module)
- `zte_epc.asn` — ZTE EPC (EpsIRIContent module, 798 lines)

### 14-Byte Huawei Header

All Huawei modes (hw-cs, hw-ims, hw-5gc, hw-sae) skip a 14-byte proprietary header before BER decoding. Structure:

| Offset | Size | Field |
|--------|------|-------|
| 0 | 1 | Sync byte (0xAA) |
| 1 | 1 | Version |
| 2 | 1 | NE type |
| 3 | 1 | Encryption flag |
| 4-5 | 2 | Payload length |
| 6-7 | 2 | Reserved/SPARE |
| 8-13 | 6 | LEA ID |

Non-Huawei modes (zte-cs, g2k, nsn-cs, zte-epc, mavenir) do NOT skip this header.

## Decompilation Notes

- `uncompyle6` on Python 3.12 could decompile Python 3.7 .pyc files with some minor issues
- The `asn_decode_api.pyc` from PYZ was 2,349 bytes → decompiled cleanly (106 lines)
- The `asn_spec.pyc` was 1,072 bytes → decompiled cleanly (63 lines)
- Main `app_v1_1.pyc` was 8,850 bytes → decompiled with good quality (371 lines)

## PYZ Standard Library Conflict

The `PYZ-00.pyz_extracted` directory contains decompiled stdlib files (argparse.py, datetime.py, json/, logging/) with invalid syntax. **Never add this dir to sys.path** — it shadows the real stdlib. Copy only custom modules (asn_decode_api.py, asn_spec.py, etc.) to a clean directory.

## Project Structure (Final)

```
~/project/ETSI-ASN1-Assistant/
├── src/
│   ├── app_linux_v3.py          # Main entry (10 decode modes)
│   ├── asn_spec_v3.py           # 9-schema loader
│   ├── asn_decode_api_v3.py     # BER decode engine
│   ├── asn_decode_iri_report_v3.py  # Post-processing
│   ├── mavenir_xml_decode.py    # XML decoder
│   ├── asnfile/                 # 24 ASN.1 files
│   └── templates/               # Flask templates
├── docs/                        # Architecture diagrams, system design
├── build/                       # Original ASN.1 backup
├── static/                      # Web assets
└── vscode/                      # Debug config
```

## Architecture Diagram

See `docs/v3_architecture.html` / `docs/v3_architecture.svg` for the full five-layer architecture visualization.
