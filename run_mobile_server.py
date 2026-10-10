"""
FoxVC Zero-Compute Static Host Server
Serves WebAssembly packages and static assets to mobile devices.
"""
import http.server
import socket
import socketserver
import os
import sys

PORT = 8080

def get_local_network_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

class StaticRootHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header("Cross-Origin-Embedder-Policy", "require-corp")
        self.send_header("Cache-Control", "no-cache, must-revalidate")
        super().end_headers()

    def do_GET(self):
        if self.path in ("/", "/index.html", "/mobile"):
            self.path = "/studio/mobile_studio.html"
        return super().do_GET()

def start_server():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    local_ip = get_local_network_ip()
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), StaticRootHandler) as httpd:
        print("\n" + "=" * 65)
        print("      FOXVC ZERO-COMPUTE MOBILE STUDIO SERVER ONLINE")
        print("=" * 65)
        print(f" PC Compute Load     : 0% (Pure static file serving)")
        print(f" Client Execution    : WebAssembly + Mobile Canvas (Client GPU/CPU)")
        print("-" * 65)
        print(f" Connect via Phone on Local Wi-Fi:")
        print(f"   http://{local_ip}:{PORT}")
        print(f" Connect via Localhost:")
        print(f"   http://localhost:{PORT}")
        print("=" * 65)
        print("Press Ctrl+C to terminate host.\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down host server.")
            httpd.server_close()

if __name__ == "__main__":
    start_server()
