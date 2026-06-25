# Decrypting Excalidraw Encrypted Share Links

Excalidraw share URLs of the form `https://excalidraw.com/#json=<docID>,<keyB64>` use **AES-128-GCM** encryption with the key encoded in the URL fragment.

## Protocol

1. **docID** — the document identifier (first segment after `#json=`)
2. **keyB64** — the decryption key, URL-safe base64 encoded (second segment)

The decrypted data is a concat-buffer format inside pako-deflate (zlib) compression.

## Full Decryption Pipeline (Node.js)

```javascript
const crypto = require('crypto');
const zlib = require('zlib');
const https = require('https');

const docId = '<docID>';
const keyB64 = '<keyB64>';

function base64urlDecode(s) {
    s = s.replace(/-/g, '+').replace(/_/g, '/');
    while (s.length % 4) s += '=';
    return Buffer.from(s, 'base64');
}

https.get(`https://json.excalidraw.com/api/v2/${docId}`, (res) => {
    const chunks = [];
    res.on('data', (c) => chunks.push(c));
    res.on('end', () => {
        const buffer = Buffer.concat(chunks);
        let offset = 0;
        const ver = buffer.readUInt32BE(offset); offset += 4;        // concat version
        const metaLen = buffer.readUInt32BE(offset); offset += 4;     // metadata length
        offset += metaLen;                                            // skip metadata
        const ivLen = buffer.readUInt32BE(offset); offset += 4;       // IV length (12)
        const iv = buffer.subarray(offset, offset + ivLen); offset += ivLen;
        const ctLen = buffer.readUInt32BE(offset); offset += 4;       // ciphertext length
        const ct = buffer.subarray(offset, offset + ctLen);

        const d = crypto.createDecipheriv('aes-128-gcm', base64urlDecode(keyB64), iv);
        d.setAuthTag(ct.subarray(-16));
        let dec = d.update(ct.subarray(0, -16));
        dec = Buffer.concat([dec, d.final()]);

        const inflated = zlib.inflateSync(dec);                      // pako = zlib inflate
        // Skip inner concat header: ver(4) + "null"-meta(4) + "null"(4) + files_len(4)
        // JSON starts at offset 16
        const firstBrace = inflated.indexOf('{'.charCodeAt(0));
        const jsonStr = inflated.subarray(firstBrace).toString('utf8');
        const parsed = JSON.parse(jsonStr);
        process.stdout.write(JSON.stringify(parsed, null, 2));
    });
}).on('error', (e) => { process.exit(1); });
```

## Data Structure

The encrypted payload fetched from `https://json.excalidraw.com/api/v2/<docID>` is a concat buffer:

```
[VERSION:4B][METADATA_LEN:4B][METADATA_JSON][IV_LEN:4B][IV:12B][CIPHERTEXT_LEN:4B][CIPHERTEXT+GCM_TAG]
```

After AES-GCM decryption, the plaintext is pako-deflate compressed. After inflate, the result is another concat buffer:

```
[VERSION:4B][x"null"_META_LEN:4B]["null":4B][FILES_LEN:4B][FILES_DATA][JSON starting at offset 16]
```

## Saving the Result

Pipe the Node.js script output to a `.excalidraw` file:

```bash
node decrypt-script.js > diagram.excalidraw
```

The file can be dragged into excalidraw.com for editing, or rendered to PNG via the `excalidraw-render` pipeline.

## Pitfalls

- The Excalidraw API endpoint (`json.excalidraw.com/api/v2/`) is the ONLY source of the encrypted data. The URL fragment alone is not enough — you MUST fetch the payload via the API.
- The API returns a 404 for non-existent documents. Handle this with a readable error.
- The `keyB64` is URL-safe base64 (uses `-` and `_` instead of `+` and `/`). Standard base64 decode will fail without replacing these characters and padding to a multiple of 4.
- The GCM authentication tag is the LAST 16 bytes of the ciphertext portion. Do not try to tag the entire `ciphertext` buffer — the first `ciphertext.length - 16` bytes are the actual ciphertext.
- pako deflate == zlib raw deflate (`zlib.inflateSync` in Node). Do NOT use `gzip` — the format is raw deflate with no gzip header.
