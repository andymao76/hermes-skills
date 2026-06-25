#!/usr/bin/env node
/**
 * Decrypt an Excalidraw encrypted share link.
 * Usage: node decrypt-share-link.js <docID> <keyB64>
 * 
 * Example:
 *   node decrypt-share-link.js XulzpJ8wVg_-Jt8ZCVOoe OHBnaDXIeRUciA-DjNySEA > diagram.excalidraw
 */
const crypto = require('crypto');
const zlib = require('zlib');
const https = require('https');

function base64urlDecode(s) {
    s = s.replace(/-/g, '+').replace(/_/g, '/');
    while (s.length % 4) s += '=';
    return Buffer.from(s, 'base64');
}

const docId = process.argv[2];
const keyB64 = process.argv[3];

if (!docId || !keyB64) {
    console.error('Usage: node decrypt-share-link.js <docID> <key>');
    process.exit(1);
}

https.get(`https://json.excalidraw.com/api/v2/${docId}`, (res) => {
    const chunks = [];
    res.on('data', (c) => chunks.push(c));
    res.on('end', () => {
        const buffer = Buffer.concat(chunks);
        let offset = 0;
        const ver = buffer.readUInt32BE(offset); offset += 4;
        const metaLen = buffer.readUInt32BE(offset); offset += 4;
        offset += metaLen;
        const ivLen = buffer.readUInt32BE(offset); offset += 4;
        const iv = buffer.subarray(offset, offset + ivLen); offset += ivLen;
        const ctLen = buffer.readUInt32BE(offset); offset += 4;
        const ct = buffer.subarray(offset, offset + ctLen);

        const d = crypto.createDecipheriv('aes-128-gcm', base64urlDecode(keyB64), iv);
        d.setAuthTag(ct.subarray(-16));
        let dec = d.update(ct.subarray(0, -16));
        dec = Buffer.concat([dec, d.final()]);

        const inflated = zlib.inflateSync(dec);
        const firstBrace = inflated.indexOf('{'.charCodeAt(0));
        const jsonStr = inflated.subarray(firstBrace).toString('utf8');
        const pretty = JSON.stringify(JSON.parse(jsonStr), null, 2);
        process.stdout.write(pretty);
    });
}).on('error', (e) => {
    console.error('Error:', e.message);
    process.exit(1);
});
