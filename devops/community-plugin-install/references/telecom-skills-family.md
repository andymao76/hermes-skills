# Telecom Standards Skill Family

Three custom skills covering the telecom standards domain, created during session 2026-06-06:

| Skill | Category | Description |
|---|---|---|
| **3gpp-expert** | research | 3GPP telecom expert (2G→6G), installed from lugasia/3gpp-skill via skills.sh. Includes 3 references: releases.md (16KB), phy-layer.md (8.6KB), working-groups.md (4KB). Covers all releases (Phase1→Rel-21), PHY layer (PSS/SSS/RACH/HARQ), and TSG/WG org structure. |
| **etsi-lawful-intercept** | research | Custom-created. Covers ETSI TC LI, TS 102 232 (7 parts), HI1/HI2/HI3, X1/X2/X3 internal interfaces, ASN.1 encoding, 5G LI evolution, TS 102 657 retained data. Paired with ~/.hermes/scripts/etsi-li-card.py for generating standards infographic. |
| **asn1-codec** | research | Custom-created. Covers BER/DER/PER/CER/XER encoding rules, TLV structure, ASN.1 grammar, 3GPP RRC/NAS and ETSI LI applications. Paired with ~/.hermes/scripts/asn1-codec.py for BER encode/decode. Depends on pyasn1 (v0.6.3) from Hermes venv. |

## Relationships

```
3GPP RRC/NAS → ASN.1 PER Aligned  → asn1-codec
ETSI LI HI2/HI3 PDU → ASN.1 PER Unaligned → asn1-codec
5G LI (TS 33.128) → etsi-lawful-intercept → references 3GPP
```

## Discovery Path

- 3gpp-expert: found via `npx skills search 3gpp` (22 installs)
- etsi-lawful-intercept: no existing skill found; custom-created based on etsi-li-card.py script
- asn1-codec: no existing skill found; custom-created with pyasn1 tooling
