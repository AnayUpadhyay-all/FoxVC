import http.server
import socketserver
import json
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from engine.runner import run_foxvc, run_foxvc_project

PORT = 8080

class FoxVCWebHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_POST(self):
        if self.path == "/api/run":
            content_len = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_len).decode("utf-8")
            try:
                data = json.loads(body)
                code = data.get("code", "")
                result = run_foxvc(code)
                resp = {
                    "success": result.success,
                    "output": result.output,
                    "error": result.error,
                    "web_output": getattr(result, "web_output", "")
                }
            except Exception as e:
                resp = {"success": False, "error": str(e), "output": ""}
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(resp).encode("utf-8"))
            return
        self.send_error(404)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self.path = "/studio/mobile_studio.html"
        super().do_GET()

def run_server(port=PORT):
    os.chdir(REPO_ROOT)
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", port), FoxVCWebHandler) as httpd:
        print(f"FoxVC Web Studio serving on port {port}...")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            httpd.server_close()

if __name__ == "__main__":
    run_server()
