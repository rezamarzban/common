import socket

def crc16_xmodem(data):
    crc = 0x0000
    for b in data:
        crc ^= (b << 8)
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc

def ack_packet(ack_prot, seq2bytes):
    # ack_prot = b'\x01'
    crc = crc16_xmodem(ack_prot + seq2bytes)
    return b'\x78\x78\x05' + ack_prot + seq2bytes + crc.to_bytes(2, 'big') + b'\x0d\x0a'

def serve(host='0.0.0.0', port=9016):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((host, port))
    s.listen(1)
    print(f"Server listening on {host}:{port}")

    while True:
        c, client_addr = s.accept()
        print(f"Connection accepted from {client_addr}")
        buf = b''

        while True:
            d = c.recv(1024)
            if not d:
                print(f"Connection closed by {client_addr}")
                break
            buf += d

            while True:
                i = buf.find(b'\x0d\x0a')
                if i < 0:
                    break
                pkt = buf[:i + 2]
                buf = buf[i + 2:]

                print(f"Received packet (hex): {pkt.hex()}")

                # 
                if pkt[-2:] != b'\x0d\x0a':
                    print("Invalid packet format.")
                    continue

                # 
                length = pkt[2]
                proto = pkt[3]

                # 
                if proto == 1:          # b'\x01'
                    print("Login packet received, sending ACK.")
                    seq = pkt[16:18]   # 
                    ack_login = ack_packet(b'\x01', seq)
                    print(f"Sent ACK packet (hex): {ack_login.hex()}")
                    c.sendall(ack_login)

                # 
                elif proto == 34:       # b'\x22'
                    # 
                    lat_bytes = pkt[11:15]
                    lon_bytes = pkt[15:19]

                    # 
                    lat_int = int.from_bytes(lat_bytes, byteorder='big', signed=True)
                    lon_int = int.from_bytes(lon_bytes, byteorder='big', signed=True)

                    # 
                    lat_deg = lat_int / 1800000.0
                    lon_deg = lon_int / 1800000.0

                    print("GPS packet received.")
                    print(f"Latitude: {lat_deg:.6f}°, Longitude: {lon_deg:.6f}°")
                    c.sendall(b'\x78\x78\x05\x22\x00\x01\x9b\x08\x0d\x0a')

        c.close()

if __name__ == "__main__":
    serve()