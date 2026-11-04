"""
Security and Execution Isolation Test Suite for FoxVC
Verifies the containment of untrusted code, filesystem boundaries,
process execution blocking, environment isolation, and Web Studio protections.
"""

import unittest
import os
import tempfile
import json
import io
from engine.shelf import SecurityPolicy, get_standard_shelf, fox_exec_cmd
from engine.runner import run_foxvc
from studio.web_studio import FoxVCWebHandler, SANDBOX_WORKSPACE


class DummyRequest:
    def __init__(self, body_bytes: bytes):
        self._io = io.BytesIO(body_bytes)

    def read(self, n):
        return self._io.read(n)


class DummyWebHandler(FoxVCWebHandler):
    """Subclass of FoxVCWebHandler for headless unit testing without network sockets."""
    def __init__(self, method: str, path: str, headers: dict, body: bytes = b""):
        self.command = method
        self.path = path
        self.headers = headers
        self.rfile = io.BytesIO(body)
        self.wfile = io.BytesIO()
        self._response_code = 0
        self._response_headers = {}

    def send_response(self, code, message=None):
        self._response_code = code

    def send_header(self, keyword, value):
        self._response_headers[keyword.lower()] = value

    def end_headers(self):
        pass

    def send_error(self, code, message=None, explain=None):
        self._response_code = code


class TestSecurityContainment(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="foxvc_sec_test_")
        self.policy = SecurityPolicy(sandboxed=True, allowed_dir=self.temp_dir)
        self.shelf = get_standard_shelf(policy=self.policy)

    def tearDown(self):
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    # 1. Process Execution Disablement
    def test_exec_cmd_disabled_in_sandbox(self):
        cmd_fn = self.shelf["execCmd"]
        res = cmd_fn("echo PWNED")
        self.assertEqual(res["ok"], 0)
        self.assertEqual(res["exit_code"], -1)
        self.assertIn("PermissionDenied", res["stderr"])

    def test_exec_cmd_script_execution_contained(self):
        code = """
res = execCmd("whoami")
emit res.ok
"""
        result = run_foxvc(code, engine_mode="interp", as_result=True, sandboxed=True, allowed_dir=self.temp_dir)
        self.assertTrue(result.success)
        self.assertEqual(result.value, 0)

    # 2. Host Environment Isolation
    def test_env_isolation_in_sandbox(self):
        # Host environment must not be exposed
        list_env_fn = self.shelf["listEnv"]
        env_pack = list_env_fn()
        # In sandboxed mode, listEnv returns isolated_env which starts empty
        self.assertNotIn("PATH", env_pack._data)
        self.assertNotIn("HOME", env_pack._data)

        # Setting env in sandbox must not mutate host os.environ
        set_env_fn = self.shelf["setEnv"]
        set_env_fn("SANDBOX_KEY", "isolated_val")
        self.assertNotIn("SANDBOX_KEY", os.environ)

        get_env_fn = self.shelf["getEnv"]
        self.assertEqual(get_env_fn("SANDBOX_KEY"), "isolated_val")

    # 3. Filesystem Path Traversal Containment
    def test_filesystem_path_traversal_blocked(self):
        write_fn = self.shelf["writeFile"]
        read_fn = self.shelf["readFile"]

        # Attempt to escape sandbox directory via ../
        outside_path = os.path.join(self.temp_dir, "..", "escaped_file.txt")
        res_write = write_fn(outside_path, "malicious_content")
        self.assertEqual(res_write, 0, "Writing outside sandbox must return 0")
        self.assertFalse(os.path.exists(outside_path))

        # Attempt to read sensitive host file
        content = read_fn("/etc/passwd")
        self.assertEqual(content, "", "Reading outside sandbox must return empty string")

    def test_allowed_dir_operations_succeed(self):
        write_fn = self.shelf["writeFile"]
        read_fn = self.shelf["readFile"]

        # Valid file within sandbox succeeds
        safe_path = os.path.join(self.temp_dir, "test.txt")
        res_write = write_fn(safe_path, "safe_data")
        self.assertEqual(res_write, 1)

        data = read_fn(safe_path)
        self.assertEqual(data, "safe_data")

    def test_recursive_remove_dir_outside_sandbox_blocked(self):
        remove_dir_fn = self.shelf["removeDir"]

        # Attempt to remove root sandbox dir or parent
        res = remove_dir_fn(self.temp_dir)
        self.assertEqual(res, 0, "Removing sandbox root must be rejected")
        self.assertTrue(os.path.exists(self.temp_dir))

    # 4. Database Confinement
    def test_database_sandbox_confinement(self):
        db_open_fn = self.shelf["dbOpen"]

        # In-memory database allowed in sandbox
        db_mem = db_open_fn(":memory:")
        self.assertEqual(db_mem["ok"], 1)

        # Database outside sandbox rejected
        db_out = db_open_fn("/tmp/unauthorized.db")
        self.assertEqual(db_out["ok"], 0)
        self.assertIn("PermissionDenied", db_out["error"])

    # 5. HTTP Server Disablement in Sandbox
    def test_http_server_disabled_in_sandbox(self):
        server_fn = self.shelf["httpServer"]
        res = server_fn(8080)
        self.assertEqual(res["ok"], 0)
        self.assertIn("PermissionDenied", res["error"])

    # 6. Web Studio Origin & CORS Protections
    def test_web_studio_untrusted_origin_rejected(self):
        handler = DummyWebHandler(
            method="POST",
            path="/api/run",
            headers={
                "Origin": "http://evil-attacker.com",
                "Content-Length": "18"
            },
            body=b'{"code": "emit 42"}'
        )
        handler.do_POST()
        self.assertEqual(handler._response_code, 403)
        self.assertIn("Untrusted Origin", handler.wfile.getvalue().decode())

    def test_web_studio_trusted_origin_accepted(self):
        body = b'{"code": "emit 42"}'
        handler = DummyWebHandler(
            method="POST",
            path="/api/run",
            headers={
                "Origin": "http://127.0.0.1:8080",
                "Content-Length": str(len(body))
            },
            body=body
        )
        handler.do_POST()
        self.assertEqual(handler._response_code, 200)
        resp_data = json.loads(handler.wfile.getvalue().decode())
        self.assertTrue(resp_data["success"])
        self.assertEqual(resp_data["value"], "42")

    def test_web_studio_arbitrary_file_read_blocked(self):
        # Attempt to read source files or credentials via GET
        handler = DummyWebHandler(
            method="GET",
            path="/engine/shelf.py",
            headers={}
        )
        handler.do_GET()
        self.assertEqual(handler._response_code, 404)

        handler2 = DummyWebHandler(
            method="GET",
            path="/.git/config",
            headers={}
        )
        handler2.do_GET()
        self.assertEqual(handler2._response_code, 404)

    # 7. Web Studio Missing Origin Protection
    def test_web_studio_missing_origin_rejected(self):
        handler = DummyWebHandler(
            method="POST",
            path="/api/run",
            headers={
                "Content-Length": "18"
            },
            body=b'{"code": "emit 42"}'
        )
        handler.do_POST()
        self.assertEqual(handler._response_code, 403)
        self.assertIn("Missing or Untrusted Origin", handler.wfile.getvalue().decode())

    # 8. Execution Timeout Enforcement
    def test_execution_timeout_enforced(self):
        # Infinite spin loop must abort when timeout is set
        code = """
spin aye
    x = 1
"""
        res = run_foxvc(code, engine_mode="interp", timeout=0.3, as_result=True)
        self.assertFalse(res.success)
        self.assertIn("timed out", str(res.error).lower())

    # 9. Outbound Network Loopback Isolation in Sandbox
    def test_outbound_loopback_blocked_in_sandbox(self):
        get_fn = self.shelf["httpGet"]
        res = get_fn("http://127.0.0.1:8080/secret")
        self.assertEqual(res["ok"], 0)
        self.assertIn("PermissionDenied", res["error"])

    # 10. Symlink Path Traversal Prevention
    def test_symlink_path_traversal_blocked(self):
        outside_file = os.path.join(tempfile.gettempdir(), "outside_target.txt")
        with open(outside_file, "w") as f:
            f.write("SECRET_HOST_DATA")
        try:
            link_path = os.path.join(self.temp_dir, "symlink_escape.txt")
            os.symlink(outside_file, link_path)

            read_fn = self.shelf["readFile"]
            content = read_fn(link_path)
            self.assertEqual(content, "", "Reading symlink escaping sandbox must return empty string")
        finally:
            if os.path.exists(outside_file):
                os.remove(outside_file)


if __name__ == '__main__':
    unittest.main()
