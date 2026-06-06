#!/usr/bin/env python3
import socket
import datetime
import struct

LOG_FILE = "/data/log.txt"
HTML_FILE = "/data/log.html"

log_fp = open(LOG_FILE, "a", encoding="utf-8")
html_fp = open(HTML_FILE, "a", encoding="utf-8")

latest_lat = None
latest_lon = None
latest_speed = None

MSG_WITH_GPS_BLOCK = {
    0x10, 0x11, 0x12, 0x22, 0x31, 0x32, 0x37, 0x16,
    0x26, 0x27, 0x1A, 0x1E, 0xA0, 0xA2, 0x17, 0x2D, 0x34,
}

MSG_ADDRESS_REQUEST = 0x2A
MSG_ADDRESS_RESPONSE = 0x97
MSG_TIME_REQUEST = 0x8A

def log(msg):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"{ts}  {msg}"
    print(line, file=log_fp, flush=True)
    print(line)

def append_uri(uri, speed, dt_str):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f'<p><a href="{uri}">{dt_str} Open map</a></p>', file=html_fp, flush=True)
    print(f"<p>Speed: {speed} km/h</p>", file=html_fp, flush=True)
    print(f"<p>DateTime: {ts}</p>", file=html_fp, flush=True)

def crc16_x25(data):
    crc = 0xFFFF
    for b in data:
        crc ^= (b << 8)
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc

def build_response(basic, msg_type, index, content=b""):
    if basic:
        header = b"\x78\x78"
        length = 5 + len(content)
        length_bytes = struct.pack("B", length)
    else:
        header = b"\x79\x79"
        length = 5 + len(content)
        length_bytes = struct.pack(">H", length)
    index_bytes = struct.pack(">H", index)
    crc_input = length_bytes + struct.pack("B", msg_type) + content + index_bytes
    crc = crc16_x25(crc_input)
    crc_bytes = struct.pack(">H", crc)
    return header + length_bytes + struct.pack("B", msg_type) + content + index_bytes + crc_bytes + b"\r\n"

def decode_gps_block(buf, offset=0):
    if len(buf) < offset + 18:
        return None
    try:
        yy, mm, dd, hh, mi, ss = struct.unpack_from("6B", buf, offset)
        year = 2000 + yy
        dt = datetime.datetime(year, mm, dd, hh, mi, ss)
        pos = offset + 6
        sats = buf[pos] & 0x0F
        pos += 1
        lat_raw = struct.unpack_from(">I", buf, pos)[0]
        pos += 4
        lon_raw = struct.unpack_from(">I", buf, pos)[0]
        pos += 4
        speed_raw = buf[pos]
        pos += 1
        flags = struct.unpack_from(">H", buf, pos)[0]
        course = flags & 0x03FF
        valid = (flags >> 12) & 1
        if not (flags & (1 << 10)):
            lat_raw = -lat_raw
        if flags & (1 << 11):
            lon_raw = -lon_raw
        lat = lat_raw / 60.0 / 30000.0
        lon = lon_raw / 60.0 / 30000.0
        return {
            "time": dt,
            "valid": valid,
            "latitude": lat,
            "longitude": lon,
            "speed": speed_raw,
            "course": course,
            "satellites": sats,
        }
    except Exception:
        return None

def extract_frame(buf):
    if len(buf) < 4:
        return None, buf
    if buf[:2] == b"\x78\x78":
        if len(buf) < 4:
            return None, buf
        data_len = buf[2]
        total = 2 + 1 + data_len + 2
        if len(buf) >= total and buf[total-2:total] == b"\r\n":
            return buf[:total], buf[total:]
    elif buf[:2] == b"\x79\x79":
        if len(buf) < 5:
            return None, buf
        data_len = struct.unpack(">H", buf[2:4])[0]
        total = 2 + 2 + data_len + 2
        if len(buf) >= total and buf[total-2:total] == b"\r\n":
            return buf[:total], buf[total:]
    idx = buf.find(b"\r\n", 1)
    if idx != -1:
        return buf[:idx+2], buf[idx+2:]
    return None, buf

def tcp_server(host="0.0.0.0", port=9016):
    global latest_lat, latest_lon, latest_speed
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host, port))
        s.listen(1)
        log(f"[TCP] Listening on {host}:{port}")
        while True:
            conn, addr = s.accept()
            log(f"[TCP] Connected by {addr}")
            buf = b""
            with conn:
                while True:
                    data = conn.recv(1024)
                    if not data:
                        log("[TCP] Connection closed by peer")
                        break
                    buf += data
                    while True:
                        pkt, buf = extract_frame(buf)
                        if pkt is None:
                            break
                        log(f"[RECV] raw={pkt.hex()}")
                        if len(pkt) < 7:
                            log("[RECV] Too short, ignoring")
                            continue
                        header = pkt[:2]
                        if header == b"\x78\x78":
                            basic = True
                            msg_type = pkt[3]
                            index = struct.unpack(">H", pkt[-6:-4])[0]
                            crc_recv = struct.unpack(">H", pkt[-4:-2])[0]
                            crc_calc = crc16_x25(pkt[2:-4])
                            payload = pkt[4:-6]
                        elif header == b"\x79\x79":
                            basic = False
                            msg_type = pkt[4]
                            index = struct.unpack(">H", pkt[-6:-4])[0]
                            crc_recv = struct.unpack(">H", pkt[-4:-2])[0]
                            crc_calc = crc16_x25(pkt[2:-4])
                            payload = pkt[5:-6]
                        else:
                            log(f"[RECV] Bad header: {header.hex()}, ignoring")
                            continue
                        if crc_calc != crc_recv:
                            log(f"[WARN] CRC mismatch: calc={crc_calc:04X} recv={crc_recv:04X} (processing anyway)")
                        log(f"[RECV] type=0x{msg_type:02X} idx={index} len={len(pkt)}")
                        if msg_type == MSG_ADDRESS_REQUEST:
                            resp_content = b"NA&&NA&&0##"
                            resp = build_response(False, MSG_ADDRESS_RESPONSE, 0, resp_content)
                            conn.sendall(resp)
                            log("[RESP] Address response")
                            continue
                        if msg_type == MSG_TIME_REQUEST:
                            now = datetime.datetime.utcnow()
                            resp_content = struct.pack(
                                "BBBBBB",
                                now.year - 2000,
                                now.month,
                                now.day,
                                now.hour,
                                now.minute,
                                now.second,
                            )
                            resp = build_response(True, MSG_TIME_REQUEST, 0, resp_content)
                            conn.sendall(resp)
                            log("[RESP] Time response")
                            continue
                        if msg_type not in (0x80, 0x81, 0x82):
                            ack = build_response(basic, msg_type, index)
                            conn.sendall(ack)
                            log(f"[ACK] 0x{msg_type:02X}")
                        if msg_type in MSG_WITH_GPS_BLOCK:
                            gps = decode_gps_block(payload, 0)
                            if gps and gps["valid"]:
                                lat = gps["latitude"]
                                lon = gps["longitude"]
                                speed = gps["speed"]
                                dt_str = gps["time"].strftime("%Y-%m-%d %H:%M:%S")
                                latest_lat, latest_lon, latest_speed = lat, lon, speed
                                log(f"[GPS] lat={lat:.6f} lon={lon:.6f} speed={speed} km/h time={dt_str}")
                                uri = f"geo:{lat:.6f},{lon:.6f};u=35"
                                append_uri(uri, speed, dt_str)
                            elif gps:
                                log("[GPS] Invalid fix")
    log("[TCP] Server stopped")

if __name__ == "__main__":
    tcp_server()