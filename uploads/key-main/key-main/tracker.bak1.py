#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
TCP → HTTP GPS Bridge (minimal version)

* TCP server  : port 9016 (your original GPS client talks here)
* HTTP server : port 80  (open a browser → shows the latest GPS coordinate)

Only the modules `socket` and `http.server` are used (plus the built‑in
`threading` for parallelism).
"""

# ----------------------------------------------------------------------
# Imports – only socket and http.server are used
# ----------------------------------------------------------------------
import socket
import http.server
import threading        # built‑in, needed for concurrency
import sys
import os

# ----------------------------------------------------------------------
# Global state (latest GPS coordinate)
# ----------------------------------------------------------------------
latest_lat = None          # in degrees
latest_lon = None
state_lock = threading.Lock()

# ----------------------------------------------------------------------
# --------- 1️⃣  TCP SERVER (your original logic, trimmed)
# ----------------------------------------------------------------------
def tcp_server(host='0.0.0.0', port=9016):
    global latest_lat, latest_lon

    def crc16_xmodem(data: bytes) -> int:
        """Same CRC function as in the original code."""
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
        return b'\x78\x78\x05' + ack_prot + seq + crc.to_bytes(2, 'big') + b'\x0d\x0a'

    # ---------- TCP socket ----------
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host, port))
        s.listen(1)
        print(f"[TCP] Listening on {host}:{port}")

        while True:                                 # accept one client at a time
            conn, addr = s.accept()
            print(f"[TCP] Connected by {addr}")
            with conn:
                buf = b''
                while True:
                    data = conn.recv(1024)
                    if not data:                    # client closed
                        print("[TCP] Connection closed by peer")
                        break
                    buf += data

                    # ---- parse complete packets (CRLF terminated) ----
                    while True:
                        end = buf.find(b'\x0d\x0a')
                        if end < 0:
                            break
                        pkt = buf[:end+2]
                        buf = buf[end+2:]

                        if pkt[-2:] != b'\x0d\x0a':
                            continue

                        proto = pkt[3]

                        # --------- GPS packet (proto 0x22) ---------
                        if proto == 34:
                            lat_b = pkt[11:15]
                            lon_b = pkt[15:19]
                            lat = int.from_bytes(lat_b, 'big', signed=True) / 1_800_000.0
                            lon = int.from_bytes(lon_b, 'big', signed=True) / 1_800_000.0
                            with state_lock:
                                latest_lat = lat
                                latest_lon = lon
                            print(f"[GPS] lat={lat:.6f}, lon={lon:.6f}")

                        # --------- ACK for other protocols ---------
                        elif proto in (1, 19):
                            seq = pkt[16:18] if proto == 1 else pkt[7:9]
                            ack = ack_packet(b'\x01' if proto == 1 else b'\x13', seq)
                            conn.sendall(ack)
                            print(f"[ACK] sent for proto {proto:#04x}")

# ----------------------------------------------------------------------
# --------- 2️⃣  HTTP SERVER (simple page with a geo: link)
# ----------------------------------------------------------------------
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
            body = (f"<h1>Current GPS Position</h1>"
                    f"<p>Latitude : {lat:.6f}°<br>"
                    f"Longitude: {lon:.6f}°</p>"
                    f'<p><a href="geo:{lat:.6f},{lon:.6f};u=35">Open map</a></p>')

        self.wfile.write(body.encode("utf-8"))

    # silence the default console log
    def log_message(self, fmt, *args):  # pragma: no cover
        return

def http_server(host='0.0.0.0', port=80):
    server = http.server.HTTPServer((host, port), GPSHandler)
    print(f"[HTTP] Listening on http://{host}:{port}/")
    server.serve_forever()

# ----------------------------------------------------------------------
# --------- 3️⃣  MAIN – run both servers in parallel
# ----------------------------------------------------------------------
if __name__ == "__main__":
    # If we’re not root, switch to a non‑privileged HTTP port
    HTTP_PORT = 80
    if os.geteuid() != 0:              # not root
        print("⚠️  Not running as root – switching HTTP port to 8080")
        HTTP_PORT = 8080

    # Start HTTP server in a background thread
    threading.Thread(target=http_server, args=("0.0.0.0", HTTP_PORT), daemon=True).start()

    # Start the TCP server (blocks forever)
    tcp_server()