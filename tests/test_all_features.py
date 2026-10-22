import unittest
import time
from engine.runner import run_foxvc_code
from engine.shelf import (
    fox_hash_sha256, fox_hash_sha512, fox_hash_md5, fox_hmac_sha256,
    fox_uuid, fox_secure_token, fox_base64_encode, fox_base64_decode,
    fox_hex_encode, fox_hex_decode, fox_get_env, fox_set_env, fox_exec_cmd,
    fox_platform, fox_cpu_count, fox_spawn, fox_await_task,
    fox_http_server, fox_http_route, fox_http_start, fox_http_stop,
    fox_http_get, fox_http_post, fox_http_response
)
from engine.runtime import FoxPack

class TestFoxVCAllFeatures(unittest.TestCase):
    # 1. Crypto & Auth
    def test_crypto_hashing(self):
        sha256 = fox_hash_sha256("foxvc")
        self.assertEqual(len(sha256), 64)

        sha512 = fox_hash_sha512("foxvc")
        self.assertEqual(len(sha512), 128)

        md5 = fox_hash_md5("foxvc")
        self.assertEqual(len(md5), 32)

        hmac_val = fox_hmac_sha256("secret_key", "payload")
        self.assertEqual(len(hmac_val), 64)

    def test_identifiers_and_tokens(self):
        u = fox_uuid()
        self.assertEqual(len(u), 36)
        self.assertIn("-", u)

        tok = fox_secure_token(16)
        self.assertEqual(len(tok), 32)

    def test_encoding(self):
        encoded = fox_base64_encode("Hello World")
        self.assertEqual(encoded, "SGVsbG8gV29ybGQ=")
        decoded = fox_base64_decode(encoded)
        self.assertEqual(decoded, "Hello World")

        hex_enc = fox_hex_encode("Fox")
        self.assertEqual(hex_enc, "466f78")
        self.assertEqual(fox_hex_decode(hex_enc), "Fox")

    # 2. System & Environment
    def test_system_and_env(self):
        fox_set_env("FOX_TEST_VAR", "active_123")
        self.assertEqual(fox_get_env("FOX_TEST_VAR"), "active_123")

        cmd_res = fox_exec_cmd("echo 'foxvc_ok'")
        self.assertEqual(cmd_res["ok"], 1)
        self.assertIn("foxvc_ok", cmd_res["stdout"])

        self.assertTrue(len(fox_platform()) > 0)
        self.assertTrue(fox_cpu_count() >= 1)

    # 3. Concurrency
    def test_concurrency(self):
        def worker(x, y):
            time.sleep(0.05)
            return x * y

        task = fox_spawn(worker, 6, 7)
        res = fox_await_task(task)
        self.assertEqual(res, 42)

    # 4. HTTP Server & REST API
    def test_http_server_and_routing(self):
        # Bind on ephemeral port 0
        srv = fox_http_server(port=0, host="127.0.0.1")

        def handle_hello(req):
            return fox_http_response(json_data=FoxPack({"message": "Hello from FoxVC Server", "client": req["method"]}))

        fox_http_route(srv, "GET", "/api/greet", handle_hello)
        started = fox_http_start(srv)
        self.assertEqual(started, 1)

        real_port = srv["port"]
        url = f"http://127.0.0.1:{real_port}/api/greet"

        resp = fox_http_get(url)
        self.assertEqual(resp["status"], 200)
        self.assertEqual(resp["ok"], 1)
        self.assertEqual(resp["json"]["message"], "Hello from FoxVC Server")
        self.assertEqual(resp["json"]["client"], "GET")

        stopped = fox_http_stop(srv)
        self.assertEqual(stopped, 1)

    # 5. Full FoxVC Script Execution
    def test_foxvc_script_suite(self):
        code = """hash = hashSha256("password123")
token = secureToken(8)
encoded = base64Encode("FoxVC Engine")
decoded = base64Decode(encoded)
say "HashLen: " + len(hash)
say "Decoded: " + decoded
setEnv("FOX_APP_ENV", "production")
env_val = getEnv("FOX_APP_ENV")
say "Env: " + env_val
"""
        res = run_foxvc_code(code)
        self.assertTrue(res["success"], f"Script failed: {res.get('error')}")
        self.assertIn("HashLen: 64", res["output"])
        self.assertIn("Decoded: FoxVC Engine", res["output"])
        self.assertIn("Env: production", res["output"])

if __name__ == "__main__":
    unittest.main()
