const net = require('net');
const fs = require('fs');
const { Buffer } = require('buffer');

// -----------------------------------------------------------------------------
// Configuration & state
// -----------------------------------------------------------------------------
const LOG_FILE = '/data/log.txt';
const HTML_FILE = '/data/log.html';

const logStream = fs.createWriteStream(LOG_FILE, { flags: 'a', encoding: 'utf8' });
const htmlStream = fs.createWriteStream(HTML_FILE, { flags: 'a', encoding: 'utf8' });

let latestLat = null;
let latestLon = null;
let latestSpeed = null;

// -----------------------------------------------------------------------------
// Constants (matching Python)
// -----------------------------------------------------------------------------
const MSG_WITH_GPS_BLOCK = new Set([
    0x10, 0x11, 0x12, 0x22, 0x31, 0x32, 0x37, 0x16,
    0x26, 0x27, 0x1A, 0x1E, 0xA0, 0xA2, 0x17, 0x2D, 0x34
]);

const MSG_ADDRESS_REQUEST  = 0x2A;
const MSG_ADDRESS_RESPONSE = 0x97;
const MSG_TIME_REQUEST     = 0x8A;

// -----------------------------------------------------------------------------
// Utility helpers
// -----------------------------------------------------------------------------
function timestamp() {
    const d = new Date();
    const pad = (n) => n.toString().padStart(2, '0');
    return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
}

function log(msg) {
    const line = `${timestamp()}  ${msg}`;
    console.log(line);
    logStream.write(line + '\n');
}

function appendUri(uri, speed, dtStr) {
    const ts = timestamp();
    htmlStream.write(`<p><a href="${uri}">${dtStr} Open map</a></p>\n`);
    htmlStream.write(`<p>Speed: ${speed} km/h</p>\n`);
    htmlStream.write(`<p>DateTime: ${ts}</p>\n`);
}

function reflectByte(b) {
    return parseInt(b.toString(2).padStart(8, '0').split('').reverse().join(''), 2);
}

// -----------------------------------------------------------------------------
// CRC‑16/X‑25 (reflected variant, exactly as in Python)
// -----------------------------------------------------------------------------
function crc16X25(data) {
    let crc = 0xFFFF;
    for (const b of data) {
        const rb = reflectByte(b);
        crc ^= (rb << 8);
        for (let i = 0; i < 8; i++) {
            if (crc & 0x8000) {
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF;
            } else {
                crc = (crc << 1) & 0xFFFF;
            }
        }
    }
    const crch = reflectByte((crc >> 8) & 0xFF);
    const crcl = reflectByte(crc & 0xFF);
    crc = (crcl << 8) | crch;
    return crc ^ 0xFFFF;
}

// -----------------------------------------------------------------------------
// Build a GT06 response packet (matching build_response in Python)
// -----------------------------------------------------------------------------
function buildResponse(basic, msgType, index, content = Buffer.alloc(0)) {
    const header = basic ? Buffer.from([0x78, 0x78]) : Buffer.from([0x79, 0x79]);
    const length = 5 + content.length;
    const lengthBytes = basic
        ? Buffer.from([length & 0xFF])
        : Buffer.from([(length >> 8) & 0xFF, length & 0xFF]);
    const indexBytes = Buffer.from([(index >> 8) & 0xFF, index & 0xFF]);

    const crcInput = Buffer.concat([lengthBytes, Buffer.from([msgType]), content, indexBytes]);
    const crc = crc16X25(crcInput);
    const crcBytes = Buffer.from([(crc >> 8) & 0xFF, crc & 0xFF]);

    return Buffer.concat([header, lengthBytes, Buffer.from([msgType]), content, indexBytes, crcBytes, Buffer.from([0x0D, 0x0A])]);
}

// -----------------------------------------------------------------------------
// Frame extraction from byte buffer
// -----------------------------------------------------------------------------
function extractFrame(buf) {
    const idx = buf.indexOf('\r\n');
    if (idx === -1) return [null, buf];
    const pkt = buf.slice(0, idx + 2);
    const rest = buf.slice(idx + 2);
    return [pkt, rest];
}

// -----------------------------------------------------------------------------
// GPS block decoder (matching decode_gps_block in Python)
// -----------------------------------------------------------------------------
function decodeGpsBlock(payload) {
    if (payload.length < 16) return null;
    try {
        const yy = payload[0], mm = payload[1], dd = payload[2],
              hh = payload[3], mi = payload[4], ss = payload[5];
        const year = 2000 + yy;
        const dtStr = `${year}-${String(mm).padStart(2,'0')}-${String(dd).padStart(2,'0')} `
                    + `${String(hh).padStart(2,'0')}:${String(mi).padStart(2,'0')}:${String(ss).padStart(2,'0')}`;

        let pos = 7; // skip satellites (byte 6 is sats & 0x0F)
        const latRaw = payload.readInt32BE(pos); pos += 4;
        const lonRaw = payload.readInt32BE(pos); pos += 4;
        const speed = payload[pos]; pos += 1;
        const flags = payload.readUInt16BE(pos);

        let lat = latRaw / 60.0 / 30000.0;
        let lon = lonRaw / 60.0 / 30000.0;
        if (!(flags & (1 << 10))) lat = -lat;
        if (flags & (1 << 11)) lon = -lon;
        const valid = (flags >> 12) & 1;
        if (!valid) return null;

        return { lat, lon, speed, dtStr };
    } catch (e) {
        return null;
    }
}

// -----------------------------------------------------------------------------
// TCP server
// -----------------------------------------------------------------------------
function tcpServer(host = '0.0.0.0', port = 9016) {
    const server = net.createServer(socket => {
        log(`[TCP] Connected by ${socket.remoteAddress}:${socket.remotePort}`);
        let rxBuf = Buffer.alloc(0);

        socket.on('data', chunk => {
            rxBuf = Buffer.concat([rxBuf, chunk]);

            while (true) {
                const [pkt, rest] = extractFrame(rxBuf.toString('binary'));
                if (!pkt) { rxBuf = Buffer.from(rest, 'binary'); break; }

                const pktBuf = Buffer.from(pkt, 'binary');
                if (pktBuf.length < 7) {
                    log(`[RECV] Too short: ${pktBuf.toString('hex')}`);
                    rxBuf = Buffer.from(rest, 'binary');
                    continue;
                }

                const header = pktBuf.slice(0, 2);
                let basic, msgType, index, crcRecv, crcCalc, payload;

                if (header.equals(Buffer.from([0x78, 0x78]))) {
                    basic = true;
                    msgType = pktBuf[3];
                    index = pktBuf.readUInt16BE(pktBuf.length - 6);
                    crcRecv = pktBuf.readUInt16BE(pktBuf.length - 4);
                    crcCalc = crc16X25(pktBuf.slice(2, pktBuf.length - 4));
                    payload = pktBuf.slice(4, pktBuf.length - 6);
                } else if (header.equals(Buffer.from([0x79, 0x79]))) {
                    basic = false;
                    msgType = pktBuf[4];
                    index = pktBuf.readUInt16BE(pktBuf.length - 6);
                    crcRecv = pktBuf.readUInt16BE(pktBuf.length - 4);
                    crcCalc = crc16X25(pktBuf.slice(2, pktBuf.length - 4));
                    payload = pktBuf.slice(5, pktBuf.length - 6);
                } else {
                    log(`[RECV] Bad header: ${header.toString('hex')}`);
                    rxBuf = Buffer.from(rest, 'binary');
                    continue;
                }

                if (crcCalc !== crcRecv) {
                    log(`[WARN] CRC mismatch: calc=${crcCalc.toString(16).padStart(4,'0')} recv=${crcRecv.toString(16).padStart(4,'0')} (processing anyway)`);
                }

                log(`[RECV] type=0x${msgType.toString(16).padStart(2,'0')} idx=${index} len=${pktBuf.length}`);

                if (msgType === MSG_ADDRESS_REQUEST) {
                    const resp = buildResponse(false, MSG_ADDRESS_RESPONSE, 0, Buffer.from('NA&&NA&&0##'));
                    socket.write(resp);
                    log('[RESP] Address response');
                } else if (msgType === MSG_TIME_REQUEST) {
                    const now = new Date();
                    const timeBuf = Buffer.from([
                        now.getUTCFullYear() - 2000,
                        now.getUTCMonth() + 1,
                        now.getUTCDate(),
                        now.getUTCHours(),
                        now.getUTCMinutes(),
                        now.getUTCSeconds()
                    ]);
                    const resp = buildResponse(true, MSG_TIME_REQUEST, 0, timeBuf);
                    socket.write(resp);
                    log('[RESP] Time response');
                } else if (msgType !== 0x80 && msgType !== 0x81 && msgType !== 0x82) {
                    const ack = buildResponse(basic, msgType, index);
                    socket.write(ack);
                    log(`[ACK] 0x${msgType.toString(16).padStart(2,'0')}`);
                }

                if (MSG_WITH_GPS_BLOCK.has(msgType)) {
                    const gps = decodeGpsBlock(payload);
                    if (gps) {
                        latestLat = gps.lat;
                        latestLon = gps.lon;
                        latestSpeed = gps.speed;
                        log(`[GPS] lat=${gps.lat.toFixed(6)} lon=${gps.lon.toFixed(6)} speed=${gps.speed} km/h time=${gps.dtStr}`);
                        const uri = `geo:${gps.lat.toFixed(6)},${gps.lon.toFixed(6)};u=35`;
                        appendUri(uri, gps.speed, gps.dtStr);
                    }
                }

                rxBuf = Buffer.from(rest, 'binary');
            }
        });

        socket.on('close', () => log('[TCP] Connection closed by peer'));
        socket.on('error', err => log(`[TCP] Socket error: ${err.message}`));
    });

    server.on('error', err => log(`[TCP] Server error: ${err.message}`));
    server.listen(port, host, () => log(`[TCP] Listening on ${host}:${port}`));
}

// -----------------------------------------------------------------------------
// Start server
// -----------------------------------------------------------------------------
if (require.main === module) {
    tcpServer();
}