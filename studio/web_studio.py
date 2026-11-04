"""
FoxVC Web Studio Server
Provides secure local mobile and browser-based coding environment with execution isolation.
"""

import http.server
import socketserver
import socket
import json
import os
import sys
import mimetypes
import tempfile
from typing import Optional

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from engine.runner import run_foxvc

PORT = 8080
HOST = "127.0.0.1"

def get_local_network_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

LOCAL_IP = get_local_network_ip()

ALLOWED_ORIGINS = {
    f"http://127.0.0.1:{PORT}",
    f"http://localhost:{PORT}",
    f"http://[::1]:{PORT}",
    f"http://{LOCAL_IP}:{PORT}",
}

SANDBOX_WORKSPACE = os.path.join(tempfile.gettempdir(), "foxvc_web_sandbox")
os.makedirs(SANDBOX_WORKSPACE, exist_ok=True)


class FoxVCWebHandler(http.server.BaseHTTPRequestHandler):
    server_version = "FoxVCWebStudio/1.0"

    def _get_allowed_origin(self) -> Optional[str]:
        origin = self.headers.get("Origin")
        if origin and origin in ALLOWED_ORIGINS:
            return origin
        return None

    def _send_cors_headers(self):
        allowed_origin = self._get_allowed_origin()
        if allowed_origin:
            self.send_header("Access-Control-Allow-Origin", allowed_origin)
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type, X-FoxVC-Client")
            self.send_header("Vary", "Origin")

    def do_OPTIONS(self):
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()

    def do_POST(self):
        if self.path == "/api/run":
            origin = self.headers.get("Origin")
            if not origin or origin not in ALLOWED_ORIGINS:
                self.send_response(403)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"success": false, "error": "Forbidden: Missing or Untrusted Origin", "output": ""}')
                return

            try:
                content_len = int(self.headers.get("Content-Length", 0))
            except ValueError:
                content_len = 0

            if content_len > 512 * 1024:  # 512 KB payload limit
                self.send_response(413)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"success": false, "error": "Payload Too Large: Script exceeds 512KB limit", "output": ""}')
                return

            body = self.rfile.read(content_len).decode("utf-8", errors="replace")
            try:
                data = json.loads(body)
                code = data.get("code", "")
                result = run_foxvc(
                    code,
                    engine_mode="interp",
                    as_result=True,
                    sandboxed=True,
                    allowed_dir=SANDBOX_WORKSPACE,
                    timeout=5.0
                )
                resp = {
                    "success": result.success,
                    "output": result.output,
                    "error": result.error,
                    "value": str(result.value) if result.value is not None else None
                }
            except Exception as e:
                resp = {"success": False, "error": str(e), "output": "", "value": None}

            resp_bytes = json.dumps(resp).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(resp_bytes)))
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(resp_bytes)
            return

        self.send_error(404, "Endpoint not found")

    def do_GET(self):
        path = self.path.split("?")[0].split("#")[0]
        file_map = {
            "/": os.path.join(REPO_ROOT, "studio", "mobile_studio.html"),
            "/index.html": os.path.join(REPO_ROOT, "studio", "mobile_studio.html"),
            "/studio/mobile_studio.html": os.path.join(REPO_ROOT, "studio", "mobile_studio.html"),
            "/manifest.json": os.path.join(REPO_ROOT, "studio", "manifest.json"),
            "/studio/web/visual_builder.js": os.path.join(REPO_ROOT, "studio", "web", "visual_builder.js"),
        }

        target_file = file_map.get(path)

        if not target_file and path.startswith("/assets/"):
            rel_asset = os.path.normpath(path[len("/assets/"):])
            if not rel_asset.startswith("..") and not os.path.isabs(rel_asset):
                cand = os.path.join(REPO_ROOT, "assets", rel_asset)
                if os.path.isfile(cand):
                    target_file = cand

        if target_file and os.path.isfile(target_file):
            ctype, _ = mimetypes.guess_type(target_file)
            ctype = ctype or "application/octet-stream"
            try:
                with open(target_file, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(content)))
                self.send_header("X-Content-Type-Options", "nosniff")
                self._send_cors_headers()
                self.end_headers()
                self.wfile.write(content)
                return
            except Exception:
                self.send_error(500, "Failed to read static file")
                return

        self.send_error(404, "File not found")


def run_server(host=None, port=PORT, network=False):
    if network or "--network" in sys.argv or "--mobile" in sys.argv:
        bind_host = "0.0.0.0"
        network = True
    else:
        bind_host = host or HOST

    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer((bind_host, port), FoxVCWebHandler) as httpd:
        print("=" * 65)
        print("          🦊 FOXVC MOBILE & WEB STUDIO ONLINE")
        print("=" * 65)
        if network or bind_host == "0.0.0.0":
            print(f" 📱 Mobile Phone (Local Wi-Fi): http://{LOCAL_IP}:{port}")
            print(f" 💻 Computer Browser:           http://localhost:{port}")
        else:
            print(f" 💻 Secure Local Loopback:     http://{bind_host}:{port}")
            print(f" (Pass '--network' or '--mobile' to allow phone connections on Wi-Fi)")
        print("=" * 65)
        print("Press Ctrl+C to stop server.\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down Web Studio.")
            httpd.server_close()


if __name__ == "__main__":
    run_server()
