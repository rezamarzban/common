#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Ultra‑lite GPS Bridge
────────────────────
• Only the modules: socket, http.server, threading
• TCP server (port 9016) – parses GPS packets (proto 0x22)
• HTTP server (port 8000) – serves a page with the latest coordinate
• log.txt   – console output (thread‑safe)
• log.html  – one line per GPS URI (thread‑safe)
"""

import socket
import http.server
import threading
import os
import datetime

# -------------------------------------------------------------------
# GLOBAL STATE (shared between TCP & HTTP threads)
# -------------------------------------------------------------------
latest_lat = None          # float in degrees
latest_lon = None
state_lock = threading.Lock()    # protects latest_lat/lon

# -------------------------------------------------------------------
# LOGGING – simple, thread‑safe, file + console
# -------------------------------------------------------------------
LOG_DIR = os.path.abspath(".")
LOG_FILE = os.path.join(LOG_DIR, "log.txt")
HTML_FILE = os.path.join(LOG_DIR, "log.html")
log_lock = threading.Lock()      # protects log file writes

def log(msg: str) -> None:
    """Append a timestamped line to log.txt (and console)."""
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"{ts}  {msg}"
    with log_lock:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    print(line)          # also echo to stdout

def append_uri(uri: str) -> None:
    """Append a GPS URI to log.html (thread‑safe)."""
    with log_lock:
        with open(HTML_FILE, "a", encoding="utf-8") as f:
            f.write(uri + "\n")

# -------------------------------------------------------------------
# CRC & ACK helpers (exactly as in your original code)
# -------------------------------------------------------------------
def crc16_xmodem(data: bytes) -> int:
    crc = 0
    for b in data:
        crc ^= (b << 8)
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc

def ack_packet(ack_prot: bytes, seq: bytes) -> bytes:
    crc = crc16_xmodem(ack_prot + seq)
    return b"\x78\x78\x05" + ack_prot + seq + crc.to_bytes(2, "big") + b"\x0d\x0a"

# -------------------------------------------------------------------
# TCP SERVER – listens for GPS packets, writes logs
# -------------------------------------------------------------------
def tcp_server(host: str = "0.0.0.0", port: int = 9016) -> None:
    global latest_lat, latest_lon

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host, port))
        s.listen(1)
        log(f"[TCP] Listening on {host}:{port}")

        while True:                                 # accept one client at a time
            conn, addr = s.accept()
            log(f"[TCP] Connected by {addr}")
            with conn:
                buf = b""
                while True:
                    data = conn.recv(1024)
                    if not data:                    # client closed
                        log("[TCP] Connection closed by peer")
                        break
                    buf += data

                    # ---- parse complete packets (CRLF terminated) ----
                    while True:
                        end = buf.find(b"\x0d\x0a")
                        if end < 0:
                            break
                        pkt = buf[: end + 2]
                        buf = buf[end + 2 :]

                        # Basic sanity check
                        if len(pkt) < 4 or pkt[-2:] != b"\x0d\x0a":
                            log("[TCP] Ignored malformed packet")
                            continue

                        proto = pkt[3]

                        # -------- GPS packet (proto 0x22) ---------
                        if proto == 34:
                            try:
                                # 4‑byte signed lat/lon
                                lat_b = pkt[11:15]
                                lon_b = pkt[15:19]
                                lat = int.from_bytes(lat_b, "big", signed=True) / 1_800_000.0
                                lon = int.from_bytes(lon_b, "big", signed=True) / 1_800_000.0
                                with state_lock:
                                    latest_lat = lat
                                    latest_lon = lon
                                log(f"[GPS] lat={lat:.6f}, lon={lon:.6f}")

                                uri = f"<a href='geo:{lat:.6f},{lon:.6f};u=35'>Open map</a>"
                                append_uri(uri)

                            except Exception as e:
                                log(f"[GPS] Error parsing packet: {e}")

                        # -------- ACK for other protocols ---------
                        elif proto in (1, 19):
                            seq = pkt[16:18] if proto == 1 else pkt[7:9]
                            ack = ack_packet(b"\x01" if proto == 1 else b"\x13", seq)
                            conn.sendall(ack)
                            log(f"[ACK] sent for proto {proto:#04x}")

# -------------------------------------------------------------------
# HTTP SERVER – simple page with the latest GPS coordinate
# -------------------------------------------------------------------
class GPSHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()

        with state_lock:
            lat = latest_lat
            lon = latest_lon

        if lat is None or lon is None:
            body = "<h1>No GPS data yet.</h1>"
        else:
            body = (
                f"<h1>Current GPS Position</h1>"
                f"<p>Latitude : {lat:.6f}°<br>"
                f"Longitude: {lon:.6f}°</p>"
                f'<p><a href="geo:{lat:.6f},{lon:.6f};u=35">Open map</a></p>'
            )

        self.wfile.write(body.encode("utf-8"))

    # silence the default console log
    def log_message(self, fmt, *args):  # pragma: no cover
        return

def http_server(host: str = "0.0.0.0", port: int = 8000) -> None:
    server = http.server.HTTPServer((host, port), GPSHandler)
    log(f"[HTTP] Listening on http://{host}:{port}/")
    server.serve_forever()

# -------------------------------------------------------------------
# MAIN – run both servers concurrently
# -------------------------------------------------------------------
if __name__ == "__main__":
    # Start HTTP server in a background thread
    threading.Thread(target=http_server, args=("0.0.0.0", 8000), daemon=True).start()

    # Start the TCP server (blocks forever)
    tcp_server()