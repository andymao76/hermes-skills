# ETSI Lawful Intercept Standards Reference

## Core Standard Series

### TS 102 232 — Handover Interface (HI2/HI3) for IP Delivery
- **Part 1**: General architecture, PDU format, ASN.1 encoding (current V3.28.1)
- **Part 2**: Email services (POP3/IMAP/SMTP)
- **Part 3**: IP bearer services (fixed broadband, WiFi)
- **Part 4**: Layer 2 network services
- **Part 5**: Multimedia services (SIP/RTP/MSRP/IMS/VoLTE)
- **Part 6**: PSTN/ISDN circuit-switched interception
- **Part 7**: Mobile networks (2G/3G/4G/5G) — sole delivery mechanism for 5G

### TS 103 221 — Internal Interception Interfaces (X1/X2/X3)
- X1: LEMF → NF provisioning (XML/SOAP)
- X2: NF → LEMF signaling (TLV, xIRI)
- X3: NF → LEMF content (TLV, xCC, high-performance)

### Other Key Standards
- **TS 101 331**: LEA requirements specification
- **TS 101 671**: Legacy circuit-switched interception (PSTN/ISDN) — marked Legacy
- **TS 102 657**: Retained data (HI-A request, HI-B delivery)
- **TS 103 120**: Administrative interface (HI1) — warrant lifecycle

## 5G LI Key Changes
- X1/X2/X3 standardized interfaces are core to 5G LI architecture
- NF-based (AMF/SMF/UPF) replaces 4G's S-GW/P-GW centralized interception
- IRI/CC payloads defined in **3GPP TS 33.128**
- Network slicing creates new LI challenges
- MEC requires local breakout interception scenarios

## Generated Card
The script `~/.hermes/scripts/etsi-li-card.py` generates a full standards overview image:
```bash
python3 ~/.hermes/scripts/etsi-li-card.py
# Output: /home/andymao/etsi-li-standards.png
```
