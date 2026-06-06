const net = require('net');
const fs  = require('fs');

const LOG_FILE  = 'log.txt';
const HTML_FILE = 'log.html';
const HOST = '0.0.0.0';
const PORT = 9016;

let latestLat   = null;
let latestLon   = null;
let latestSpeed = null;

const logStream  = fs.createWriteStream(LOG_FILE,  { flags: 'a', encoding: 'utf8' });
const htmlStream = fs.createWriteStream(HTML_FILE, { flags: 'a', encoding: 'utf8' });

function log(msg) {
    const ts = new Date().toISOString().replace('T', ' ').substr(0, 19);
    const out = `${ts}  ${msg}`;
    console.log(out);
    logStream.write(out + '\n');
}

function appendUri(uri, speed) {
    const ts = new Date().toISOString().replace('T', ' ').substr(0, 19);
    htmlStream.write(`<p><a href="${uri}">${ts} Open map</a></p>\n`);
    htmlStream.write(`<p>Speed: ${speed} km/h</p>\n`);
}

function crc16XModem(data) {
    let crc = 0x0000;
    for (const b of data) {
        crc ^= (b << 8);
        for (let i = 0; i < 8; i++) {
            crc = (crc & 0x8000) ?
                ((crc << 1) ^ 0x1021) :
                (crc << 1);
            crc &= 0xFFFF;
        }
    }
    return crc;
}

function ackPacket(ackProt, seq) {
    const body = Buffer.concat([Buffer.from([0x78, 0x78, 0x05]), ackProt, seq]);
    const crc   = crc16XModem(body);
    const crcBuf = Buffer.alloc(2);
    crcBuf.writeUInt16BE(crc, 0);
    return Buffer.concat([body, crcBuf, Buffer.from([0x0D, 0x0A])]);
}

function readSignedInt32(buf, offset) {
    return buf.readInt32BE(offset) / 1_800_000.0;
}

function tcpServer() {
    const server = net.createServer((socket) => {
        log(`[TCP] Connected by ${socket.remoteAddress}:${socket.remotePort}`);
        let rxBuf = Buffer.alloc(0);

        socket.on('data', (chunk) => {
            rxBuf = Buffer.concat([rxBuf, chunk]);

            let idx;
            while ((idx = rxBuf.indexOf('\r\n')) !== -1) {
                const pkt = rxBuf.slice(0, idx + 2);
                rxBuf = rxBuf.slice(idx + 2);

                if (pkt.length < 4 || pkt[pkt.length - 2] !== 0x0D || pkt[pkt.length - 1] !== 0x0A) {
                    log('[TCP] Ignored malformed packet');
                    continue;
                }

                const proto = pkt[3];
                log(`[RECV] pkt=${pkt.toString('hex')}`);

                if (proto === 34) {
                    try {
                        const lat   = readSignedInt32(pkt, 11);
                        const lon   = readSignedInt32(pkt, 15);
                        const speed = pkt.length > 19 ? pkt[19] : 0;
                        latestLat   = lat;
                        latestLon   = lon;
                        latestSpeed = speed;

                        log(`[GPS] lat=${lat.toFixed(6)}, lon=${lon.toFixed(6)}, speed=${speed} km/h`);
                        const uri = `geo:${lat.toFixed(6)},${lon.toFixed(6)};u=35`;
                        appendUri(uri, speed);
                    } catch (e) {
                        log(`[GPS] Error parsing packet: ${e.message}`);
                    }
                } else if (proto === 1 || proto === 19) {
                    const seq = proto === 1
                        ? pkt.slice(16, 18)
                        : pkt.slice(7, 9);
                    const ackProt = proto === 1 ? Buffer.from([0x01]) : Buffer.from([0x13]);
                    const ack = ackPacket(ackProt, seq);
                    socket.write(ack);
                    log(`[ACK] sent for proto ${proto.toString(16).padStart(2, '0')}`);
                }
            }
        });

        socket.on('close', () => {
            log('[TCP] Connection closed by peer');
        });

        socket.on('error', (err) => {
            log(`[TCP] Socket error: ${err.message}`);
        });
    });

    server.on('error', (err) => {
        log(`[TCP] Server error: ${err.message}`);
    });

    server.listen(PORT, HOST, () => {
        log(`[TCP] Listening on ${HOST}:${PORT}`);
    });
}

if (require.main === module) {
    tcpServer();
}