#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import datetime

LOG_FILE = "/data/log.txt"
HTML_FILE = "/data/log.html"

log_fp = open(LOG_FILE,  "a", encoding="utf-8")
html_fp = open(HTML_FILE, "a", encoding="utf-8")

latest_lat   = None
latest_lon   = None
latest_speed = None

def log(msg: str) -> None:
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{ts}  {msg}", file=log_fp, flush=True)
    print(f"{ts}  {msg}")

def append_uri(uri: str, speed: int, dt_str: str) -> None:
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f'<p><a href="{uri}">{dt_str} Open map</a></p>', file=html_fp, flush=True)
    print(f"<p>Speed: {speed} km/h</p>", file=html_fp, flush=True)
    print(f"<p>DateTime: {ts}</p>", file=html_fp, flush=True)

def crc16_xmodem(data: bytes) -> int:
    crc = 0
    for b in data:
        crc ^= (b << 8)
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return crc

def ack_packet(ack_prot: bytes, seq: bytes) -> bytes:
    crc = crc16_xmodem(ack_prot + seq)
    return b"\x78\x78\x05" + ack_prot + seq + crc.to_bytes(2, "big") + b"\x0d\x0a"

def tcp_server(host: str = "0.0.0.0", port: int = 9016) -> None:
    global latest_lat, latest_lon, latest_speed

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host, port))
        s.listen(1)
        log(f"[TCP] Listening on {host}:{port}")

        while True:
            conn, addr = s.accept()
            log(f"[TCP] Connected by {addr}")
            with conn:
                buf = b""
                while True:
                    data = conn.recv(1024)
                    if not data:
                        log("[TCP] Connection closed by peer")
                        break
                    buf += data
                    while True:
                        end = buf.find(b"\x0d\x0a")
                        if end < 0:
                            break
                        pkt = buf[: end + 2]
                        buf = buf[end + 2 :]
                        if len(pkt) < 4 or pkt[-2:] != b"\x0d\x0a":
                            log("[TCP] Ignored malformed packet")
                            continue
                        proto = pkt[3]
                        log(f"[RECV] pkt={pkt.hex()}")
                        if proto == 34:
                            try:
                                # Extract latitude, longitude
                                lat = int.from_bytes(pkt[11:15], "big", signed=True) / 1_800_000.0
                                lon = int.from_bytes(pkt[15:19], "big", signed=True) / 1_800_000.0
                                # Extract speed
                                speed = pkt[19] if len(pkt) > 19 else 0
                                # Extract DateTime from pkt[4:10]
                                yy, mm, dd, hh, mi, ss = pkt[4:10]
                                year = 2020 + yy  # assume 2020‑based year
                                dt_obj = datetime.datetime(year, mm, dd, hh, mi, ss)
                                dt_str = dt_obj.strftime("%Y-%m-%d %H:%M:%S")
                                latest_lat, latest_lon, latest_speed = lat, lon, speed
                                log(f"[GPS] lat={lat:.6f}, lon={lon:.6f}, speed={speed} km/h, datetime={dt_str}")
                                uri = f"geo:{lat:.6f},{lon:.6f};u=35"
                                append_uri(uri, speed, dt_str)
                            except Exception as e:
                                log(f"[GPS] Error parsing packet: {e}")
                        elif proto in (1, 19):
                            seq = pkt[16:18] if proto == 1 else pkt[7:9]
                            ack = ack_packet(b"\x01" if proto == 1 else b"\x13", seq)
                            conn.sendall(ack)
                            log(f"[ACK] sent for proto {proto:#04x}")

if __name__ == "__main__":
    tcp_server()