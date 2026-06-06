import http.server, socketserver, base64, urllib.parse

LOG_FILE = "/data/log.html"
PASSWORD = "mysecretpassword"
PORT = 3000

def decrypt(data, pwd):
    try:
        l_hex, e_hex = data.split(':')
        l, e, p = int(bytes.fromhex(l_hex).hex(), 16), int(e_hex, 16), int(bytes(pwd, 'utf-8').hex(), 16)
        return base64.b64decode(int(e // p).to_bytes(l, 'big')).decode()
    except: return None

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        try:
            with open(LOG_FILE, "r") as f: lines = f.readlines()
            uri = decrypt(lines[-3].split('"')[1], PASSWORD)
            speed = lines[-2].split("Speed: ")[1].split(" ")[0]
            link = f'<a href="{uri}">Map</a>'
        except: link, speed = "Error", "N/A"
        
        self.send_response(200)
        self.end_headers()
        self.wfile.write(f"<html><body><p>Speed: {speed} km/h</p><p>Link: {link}</p></body></html>".encode())

    def log_message(self, format, *args): pass

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    httpd.serve_forever()
