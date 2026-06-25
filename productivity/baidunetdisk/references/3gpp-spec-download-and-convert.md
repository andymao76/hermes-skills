# 3GPP Spec Download + Markdown Conversion

## FTP Download

```
https://www.3gpp.org/ftp/Specs/archive/33_series/<spec_number>/<file>.zip
```

Release suffix mapping: `-i00`=R19, `-h00`=R18, `-g00`=R17, `-f00`=R16, ...

Example for TS 33.108 R19: `33108-i00.zip`

### Download command

```bash
curl -L -o 33108-i00.zip "https://www.3gpp.org/ftp/Specs/archive/33_series/33.108/33108-i00.zip"
```

## Extraction

```bash
unzip 33108-i00.zip
# → 33108-i00.docx (main spec)
# → 33108-i00-attachments.zip (ASN.1 files)

unzip 33108-i00-attachments.zip -d ts33108-asn1/
```

## Convert to Markdown

```bash
# Modern releases (.docx format):
pip install markitdown[docx]  # needs mammoth + lxml
markitdown 33108-i00.docx > ts33108.md

# Older releases (.doc / OLE2 format — e.g. TS 33.126 R18):
# markitdown does NOT support .doc directly
libreoffice --headless --convert-to docx 33126-i00.doc
markitdown 33126-i00.docx > ts33126.md
```

## Store to Knowledge Base

```bash
mkdir -p ~/knowledge/3gpp-ts33108
cp ts33108.md ~/knowledge/3gpp-ts33108/
cp -r ts33108-asn1 ~/knowledge/3gpp-ts33108/asn1
```

## Files Already Downloaded

| Spec | Version | Path | Size |
|------|---------|------|------|
| TS 33.108 | V18.0.0 | ~/knowledge/3gpp-ts33108/ | 787KB md + 19 ASN.1 |
| TS 33.127 | V18.0.0 | ~/knowledge/3gpp-references/ | 349KB md |
| TS 33.126 | V18.0.0 | ~/knowledge/3gpp-references/ | 51KB md |

## Key Discovery

3GPP TS 33.108/127 define **HI1/HI2/HI3** (Handover Interface for LIG→LEMF delivery).
**X1** is CSP-internal (vendor proprietary) — not in 3GPP scope.
TS 33.127 defines LI_X1 as LIPF↔POI/TF/MDF provisioning interface (4 sub-interfaces).
