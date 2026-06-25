# BER Encoding Reference — 3GPP Protocol Analysis

> Sources: ITU-T X.690 (02/2021), OSS Nokalva BER Quick Reference, pyasn1 0.6.3
> Local PDFs: `knowledge/telecom/3gpp/ITU-T_X.690-202102_BER.pdf` (822K)
> Analysis script: `~/ber-tag-analyzer.py`

## BER Tag Encoding (X.690 §8.1.2)

**Identifier octet structure:**
```
bits 7-6: Class     00=Universal, 01=Application, 10=Context-specific, 11=Private
bit 5:    Form      0=Primitive, 1=Constructed
bits 4-0: Tag#      ≤30 short form, =11111 long form marker
```

**Short form (tag ≤ 30):** `TAG = byte & 0x1F`

**Long form (tag ≥ 31):** First byte low 5 bits = 11111. Continuation bytes:
- Each byte bit 7 = 1 (more) / 0 (last)
- Lower 7 bits concatenated big-endian

## BER Length Encoding (X.690 §8.1.3)

| Format | Condition | Encoding |
|--------|-----------|----------|
| Short | 0-127 | Single byte, bit7=0, length in bits 6-0 |
| Long | 128+ | First byte bit7=1, bits 6-0 = num follow bytes; then big-endian length |
| Indefinite | constructed only | `0x80` ... content ... `00 00` (EOC) |

## Common Universal Tags

| Type | Tag | Encoding |
|------|:---:|----------|
| BOOLEAN | 1 | TRUE=any non-zero, FALSE=00 |
| INTEGER | 2 | 2's complement, big-endian, minimal octets |
| BIT STRING | 3 | First octet = unused bits count |
| OCTET STRING | 4 | Raw bytes |
| NULL | 5 | No value (length=0) |
| ENUMERATED | 10 | Same as INTEGER encoding |
| SEQUENCE / SEQUENCE OF | 16 | Constructed |
| SET / SET OF | 17 | Constructed |

## MAP Protocol Analysis (TS 29.002)

MAP messages use apReq_T header (proprietary structure) wrapping BER-encoded ASN.1 content.

**apReq_T structure:**
```
typedef struct {
    WORD  DigId;       // dialog ID
    BYTE  InvkId;      // invocation ID
    BYTE  OpCode;      // operation code (e.g. 0x07 = insertSubscriberData)
    BYTE  LinkIdFg;    // link ID flag
    BYTE  LinkId;      // link ID
    BYTE  IndMsgSeg;   // 1=TC_Continue, 0=TC_End
    BYTE  LastMessage; // 1=final component
    WORD  CodeLen;     // ASN.1 content length
    BYTE  CodeContent[]; // ASN.1 BER payload
} _PACKED_1_;
```

**Common MAP OpCodes (TS 29.002):**
- 0x02: updateLocation
- 0x05: sendAuthenticationInfo
- **0x07: insertSubscriberData**
- 0x44: cancelLocation

## Verification: Use pyasn1, NOT LLMs

```python
from pyasn1.codec.ber import decoder
from pyasn1.type import univ

# Decode without schema
decoded, remainder = decoder.decode(data, asn1Spec=univ.Any())
```

**LLMs (Qwen/DeepSeek) are unreliable for BER verification.** 
- DeepSeek-V3 reversed BearerService/Teleservice fields and decoded IMSI incorrectly
- Qwen3.5 missed structural nodes (B0 21 SubscriberData)
- BER is deterministic bit manipulation — use pyasn1 or `ber-tag-analyzer.py`

## Pitfalls

1. **`length == 0` does NOT mean end of data.** NULL types have length=0 but the TLV continues. Do NOT break on length=0.
2. **TBCD IMSI decoding is error-prone.** Always verify with a tool. `64 10 00 00 00 00 20 F4` → IMSI = 46010000000024.
3. **apReq_T header is NOT BER.** MAP PDUs have 10-byte proprietary header before the ASN.1 BER content. Strip it before BER decoding.
4. **Constructed vs Primitive matters.** `B0` ([16] constructed) wraps children; `90` ([16] primitive) is a leaf.
