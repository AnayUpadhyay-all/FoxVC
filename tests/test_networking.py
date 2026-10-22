import unittest
import threading
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from engine.runner import run_foxvc_code
from engine.shelf import fox_url_encode, fox_url_decode, fox_http_get, fox_http_post, fox_fetch, fox_json_parse
from engine.runtime import FoxPack

class MockServerHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Suppress server logs during test

    def do_GET(self):
        if self.path == "/api/status":
            body = json.dumps({"status": "online", "version": "0.5.0", "items": [1, 2, 3]}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/api/text":
            body = b"plain text response"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body_bytes = self.rfile.read(content_length) if content_length > 0 else b""
        req_json = {}
        try:
            req_json = json.loads(body_bytes.decode("utf-8"))
        except Exception:
            pass

        resp = json.dumps({"received": req_json, "echo": True}).encode("utf-8")
        self.send_response(201)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(resp)))
        self.end_headers()
        self.wfile.write(resp)

class TestFoxVCNetworking(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = HTTPServer(("127.0.0.1", 0), MockServerHandler)
        cls.port = cls.server.server_port
        cls.server_thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def test_url_encoding(self):
        encoded = fox_url_encode(FoxPack({"query": "hello world", "page": 1}))
        self.assertIn("query=hello+world", encoded)
        self.assertIn("page=1", encoded)

        decoded = fox_url_decode("hello+world%21")
        self.assertEqual(decoded, "hello world!")

    def test_json_parse_returns_foxpack(self):
        parsed = fox_json_parse('{"name": "FoxVC", "speed": 100}')
        self.assertIsInstance(parsed, FoxPack)
        self.assertEqual(parsed["name"], "FoxVC")
        self.assertEqual(parsed["speed"], 100)

    def test_http_get_in_shelf(self):
        url = f"http://127.0.0.1:{self.port}/api/status"
        res = fox_http_get(url)
        self.assertEqual(res["status"], 200)
        self.assertEqual(res["ok"], 1)
        self.assertIn("status", res["json"])
        self.assertEqual(res["json"]["status"], "online")

    def test_http_post_in_shelf(self):
        url = f"http://127.0.0.1:{self.port}/api/create"
        res = fox_http_post(url, body=FoxPack({"user": "fox_dev", "role": "admin"}))
        self.assertEqual(res["status"], 201)
        self.assertEqual(res["ok"], 1)
        self.assertEqual(res["json"]["received"]["user"], "fox_dev")

    def test_foxvc_script_fetch_execution(self):
        url = f"http://127.0.0.1:{self.port}/api/text"
        code = f"""res = httpGet("{url}")
say res.ok
say res.body
"""
        res = run_foxvc_code(code)
        self.assertTrue(res["success"], f"Script failed: {res.get('error')}")
        self.assertIn("1", res["output"])
        self.assertIn("plain text response", res["output"])

if __name__ == "__main__":
    unittest.main()
