"""
Unit tests for FoxCloud Gaming Host Server & Mobile Client Assets.
Verifies server endpoints, static files, and remote input dispatch.
"""

import unittest
import socket
import threading
import time
import urllib.request
import json
import os

from cloud_gaming.server import ThreadedTCPServer, CloudGamingHandler, get_local_wifi_ip, WEB_DIR


class TestCloudGamingServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.port = 18888
        cls.httpd = ThreadedTCPServer(("127.0.0.1", cls.port), CloudGamingHandler)
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.port}"
        time.sleep(0.3)

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()

    def test_local_ip_detection(self):
        ip = get_local_wifi_ip()
        self.assertIsInstance(ip, str)
        self.assertTrue(len(ip.split(".")) == 4)

    def test_serve_index_html(self):
        url = f"{self.base_url}/"
        with urllib.request.urlopen(url, timeout=3.0) as resp:
            self.assertEqual(resp.status, 200)
            self.assertIn("text/html", resp.headers.get("Content-Type", ""))
            content = resp.read().decode("utf-8")
            self.assertIn("FoxCloud Gaming", content)
            self.assertIn("joystickZone", content)
            self.assertIn("btnA", content)

    def test_serve_games_js(self):
        url = f"{self.base_url}/games.js"
        with urllib.request.urlopen(url, timeout=3.0) as resp:
            self.assertEqual(resp.status, 200)
            content = resp.read().decode("utf-8")
            self.assertIn("SpaceDefender", content)
            self.assertIn("CyberSnake", content)
            self.assertIn("FoxRunner", content)
            self.assertIn("CyberPong", content)

    def test_serve_manifest_json(self):
        url = f"{self.base_url}/manifest.json"
        with urllib.request.urlopen(url, timeout=3.0) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(data["name"], "FoxCloud Gaming")
            self.assertEqual(data["display"], "standalone")

    def test_api_status(self):
        url = f"{self.base_url}/api/status"
        with urllib.request.urlopen(url, timeout=3.0) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(data["status"], "online")
            self.assertIn("host_device", data)
            self.assertIn("cpu_cores", data)

    def test_api_games(self):
        url = f"{self.base_url}/api/games"
        with urllib.request.urlopen(url, timeout=3.0) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(data["count"], 4)
            self.assertEqual(data["supported_fps"], 60)

    def test_api_input_post(self):
        url = f"{self.base_url}/api/input"
        payload = json.dumps({"stickX": 0.5, "stickY": -0.8, "btnA": True}).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertTrue(data.get("received"))


if __name__ == "__main__":
    unittest.main()
