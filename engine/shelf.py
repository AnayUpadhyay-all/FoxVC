
from typing import Dict, Any, List, Optional
import os
import sys
import math
import time
import json
import random
import ctypes
import urllib.request
import urllib.error
import urllib.parse
import ssl
import http.server
import threading
import hashlib
import hmac
import uuid
import base64
import secrets
import subprocess
import concurrent.futures
from .runtime import FoxPack

# Universal Collection Primitives (General-Purpose, Zero Game Assumptions)
def fox_pack(*args):
    # Dynamic list constructor: pack() or pack(initial_cap)
    if len(args) == 0:
        return []
    if len(args) == 1 and isinstance(args[0], (int, float)):
        return [0.0] * int(args[0])
    return list(args)

def fox_push(lst, item):
    if isinstance(lst, list):
        lst.append(item)
    return lst

def fox_pop(lst):
    if isinstance(lst, list) and len(lst) > 0:
        return lst.pop()
    return 0

def fox_remove_at(lst, idx):
    if isinstance(lst, list) and 0 <= int(idx) < len(lst):
        return lst.pop(int(idx))
    return 0


def fox_get_mouse_x():
    if _raylib:
        return _raylib.GetMouseX()
    return 0

def fox_get_mouse_y():
    if _raylib:
        return _raylib.GetMouseY()
    return 0

def fox_mouse_down(btn=0):
    if _raylib:
        return 1 if _raylib.IsMouseButtonDown(int(btn)) else 0
    return 0


import ctypes
import os

# Load Native Raylib Shared Library
_lib_dir = os.path.join(os.path.dirname(__file__), "lib")
_libraylib_path = os.path.join(_lib_dir, "libraylib.so")
_raylib = None

try:
    _raylib = ctypes.CDLL(_libraylib_path, mode=ctypes.RTLD_GLOBAL)
    
    # Declare function prototypes
    _raylib.InitWindow.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_char_p]
    _raylib.InitWindow.restype = None
    _raylib.SetTargetFPS.argtypes = [ctypes.c_int]
    _raylib.SetTargetFPS.restype = None
    _raylib.WindowShouldClose.argtypes = []
    _raylib.WindowShouldClose.restype = ctypes.c_bool
    _raylib.CloseWindow.argtypes = []
    _raylib.CloseWindow.restype = None
    _raylib.BeginDrawing.argtypes = []
    _raylib.BeginDrawing.restype = None
    _raylib.EndDrawing.argtypes = []
    _raylib.EndDrawing.restype = None
    _raylib.ClearBackground.argtypes = [ctypes.c_uint32]
    _raylib.ClearBackground.restype = None
    _raylib.DrawRectangle.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_uint32]
    _raylib.DrawRectangle.restype = None
    _raylib.IsKeyDown.argtypes = [ctypes.c_int]
    _raylib.IsKeyDown.restype = ctypes.c_bool
    _raylib.DrawCircle.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_float, ctypes.c_uint32]
    _raylib.DrawCircle.restype = None
    _raylib.DrawLine.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_uint32]
    _raylib.DrawLine.restype = None
    _raylib.DrawText.argtypes = [ctypes.c_char_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_uint32]
    _raylib.DrawText.restype = None
    _raylib.GetFPS.argtypes = []
    _raylib.GetFPS.restype = ctypes.c_int
    _raylib.IsKeyPressed.argtypes = [ctypes.c_int]
    _raylib.IsKeyPressed.restype = ctypes.c_bool
    _raylib.IsMouseButtonPressed.argtypes = [ctypes.c_int]
    _raylib.IsMouseButtonPressed.restype = ctypes.c_bool
except Exception as e:
    pass


def fox_close_window():
    if _raylib and _raylib.IsWindowReady():
        _raylib.CloseWindow()
    return 1

def fox_open_window(w, h, title="FoxVC Game"):
    if _raylib:
        _raylib.InitWindow(int(w), int(h), str(title).encode("utf-8"))
        _raylib.SetTargetFPS(60)
    return 1

def fox_window_closed():
    if _raylib:
        return 1 if _raylib.WindowShouldClose() else 0
    return 1

def fox_start_frame():
    if _raylib:
        _raylib.BeginDrawing()
        # 0xFF19120F = Dark slate background in RGBA/ABGR
        _raylib.ClearBackground(0xFF19120F)
    return 1

def fox_end_frame():
    if _raylib:
        _raylib.EndDrawing()
    return 1

def fox_draw_box(x, y, w, h, col=1):
    if _raylib:
        # Colors: 1 = Orange (0xFF00A5FF), 2 = Green (0xFF00E600), 3 = Red (0xFF0000FF), 0 = White (0xFFFFFFFF)
        c = 0xFF00A5FF
        if int(col) == 2:
            c = 0xFF00E600
        elif int(col) == 3:
            c = 0xFF0000FF
        elif int(col) == 0:
            c = 0xFFFFFFFF
        _raylib.DrawRectangle(int(x), int(y), int(w), int(h), c)
    return 1

def fox_is_key_down(key):
    if _raylib:
        return 1 if _raylib.IsKeyDown(int(key)) else 0
    return 0

def fox_draw_circle(cx, cy, radius, col=1):
    if _raylib:
        _raylib.DrawCircle(int(cx), int(cy), float(radius), _get_uint_color(col))
    return 1

def fox_draw_line(x1, y1, x2, y2, col=1):
    if _raylib:
        _raylib.DrawLine(int(x1), int(y1), int(x2), int(y2), _get_uint_color(col))
    return 1

def fox_draw_text(text, x, y, size=20, col=0):
    if _raylib:
        _raylib.DrawText(str(text).encode("utf-8"), int(x), int(y), int(size), _get_uint_color(col))
    return 1

def fox_get_fps():
    if _raylib:
        return _raylib.GetFPS()
    return 60

def fox_set_fps(fps):
    if _raylib:
        _raylib.SetTargetFPS(int(fps))
    return 1

def fox_is_key_pressed(key):
    if _raylib:
        return 1 if _raylib.IsKeyPressed(int(key)) else 0
    return 0

def fox_mouse_clicked(btn=0):
    if _raylib:
        return 1 if _raylib.IsMouseButtonPressed(int(btn)) else 0
    return 0

def _get_uint_color(col):
    colors = {
        0: 0xFFFFFFFF, # White
        1: 0xFF00A5FF, # Orange
        2: 0xFF00E600, # Green
        3: 0xFF0000FF, # Red
        4: 0xFFFF5500, # Blue
        5: 0xFF00E5FF, # Yellow
        6: 0xFFFF00CC, # Purple
        7: 0xFF000000, # Black
    }
    return colors.get(int(col), 0xFFFFFFFF)

# File System I/O
def fox_read_file(path):
    try:
        with open(str(path), "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""

def fox_write_file(path, content):
    try:
        with open(str(path), "w", encoding="utf-8") as f:
            f.write(str(content))
        return 1
    except Exception:
        return 0

def fox_append_file(path, content):
    try:
        with open(str(path), "a", encoding="utf-8") as f:
            f.write(str(content))
        return 1
    except Exception:
        return 0

def fox_file_exists(path):
    return 1 if os.path.exists(str(path)) else 0

def fox_remove_file(path):
    try:
        if os.path.exists(str(path)):
            os.remove(str(path))
            return 1
    except Exception:
        pass
    return 0

def fox_list_dir(path="."):
    try:
        return os.listdir(str(path))
    except Exception:
        return []

import urllib.request
import urllib.error
import urllib.parse
import ssl
from .runtime import FoxPack

def to_fox_val(val):
    if isinstance(val, dict):
        return FoxPack({k: to_fox_val(v) for k, v in val.items()})
    elif isinstance(val, list):
        return [to_fox_val(x) for x in val]
    return val

def _clean_obj(o):
    if hasattr(o, "_data"):
        return {k: _clean_obj(v) for k, v in o._data.items()}
    if isinstance(o, list):
        return [_clean_obj(x) for x in o]
    return o

# JSON Data
def fox_json_parse(text):
    try:
        raw = json.loads(str(text))
        return to_fox_val(raw)
    except Exception:
        return FoxPack({})

def fox_json_string(obj, indent=0):
    try:
        if indent > 0:
            return json.dumps(_clean_obj(obj), indent=int(indent))
        return json.dumps(_clean_obj(obj))
    except Exception:
        return "{}"

# Outbound HTTP & Networking
def fox_http_request(url, method="GET", body=None, headers=None, timeout=10.0):
    url_str = str(url)
    method_str = str(method).upper()
    req_headers = {}

    if hasattr(headers, "_data"):
        req_headers = {str(k): str(v) for k, v in headers._data.items()}
    elif isinstance(headers, dict):
        req_headers = {str(k): str(v) for k, v in headers.items()}

    data_bytes = None
    if body is not None:
        if isinstance(body, str):
            data_bytes = body.encode("utf-8")
        elif hasattr(body, "_data") or isinstance(body, (dict, list)):
            data_bytes = json.dumps(_clean_obj(body)).encode("utf-8")
            if "Content-Type" not in req_headers and "content-type" not in req_headers:
                req_headers["Content-Type"] = "application/json"
        else:
            data_bytes = str(body).encode("utf-8")

    if "User-Agent" not in req_headers and "user-agent" not in req_headers:
        req_headers["User-Agent"] = "FoxVC/0.5 (NetworkingEngine)"

    try:
        req = urllib.request.Request(url_str, data=data_bytes, headers=req_headers, method=method_str)
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        with urllib.request.urlopen(req, timeout=float(timeout), context=ctx) as resp:
            status = resp.status
            resp_bytes = resp.read()
            body_str = resp_bytes.decode("utf-8", errors="replace")
            resp_headers = {k.lower(): v for k, v in resp.getheaders()}

            parsed_json = None
            try:
                parsed_json = to_fox_val(json.loads(body_str))
            except Exception:
                pass

            return FoxPack({
                "status": status,
                "ok": 1 if 200 <= status < 300 else 0,
                "body": body_str,
                "headers": FoxPack(resp_headers),
                "json": parsed_json if parsed_json is not None else FoxPack({}),
                "error": ""
            })
    except urllib.error.HTTPError as e:
        err_body = ""
        try:
            err_body = e.read().decode("utf-8", errors="replace")
        except Exception:
            pass
        parsed_json = None
        try:
            parsed_json = to_fox_val(json.loads(err_body))
        except Exception:
            pass
        return FoxPack({
            "status": e.code,
            "ok": 0,
            "body": err_body,
            "headers": FoxPack({k.lower(): v for k, v in e.headers.items()}),
            "json": parsed_json if parsed_json is not None else FoxPack({}),
            "error": str(e)
        })
    except Exception as e:
        return FoxPack({
            "status": 0,
            "ok": 0,
            "body": "",
            "headers": FoxPack({}),
            "json": FoxPack({}),
            "error": str(e)
        })

def fox_http_get(url, headers=None, timeout=10.0):
    return fox_http_request(url, method="GET", headers=headers, timeout=timeout)

def fox_http_post(url, body=None, headers=None, timeout=10.0):
    return fox_http_request(url, method="POST", body=body, headers=headers, timeout=timeout)

def fox_http_put(url, body=None, headers=None, timeout=10.0):
    return fox_http_request(url, method="PUT", body=body, headers=headers, timeout=timeout)

def fox_http_delete(url, headers=None, timeout=10.0):
    return fox_http_request(url, method="DELETE", headers=headers, timeout=timeout)

def fox_fetch(url, options=None):
    method = "GET"
    body = None
    headers = None
    timeout = 10.0
    if options is not None:
        if hasattr(options, "_data"):
            opts = options._data
        elif isinstance(options, dict):
            opts = options
        else:
            opts = {}
        method = opts.get("method", "GET")
        body = opts.get("body", None)
        headers = opts.get("headers", None)
        timeout = float(opts.get("timeout", 10.0))
    return fox_http_request(url, method=method, body=body, headers=headers, timeout=timeout)

def fox_url_encode(params):
    try:
        clean = _clean_obj(params)
        if isinstance(clean, dict):
            return urllib.parse.urlencode(clean)
        return str(params)
    except Exception:
        return ""

def fox_url_decode(s):
    try:
        return urllib.parse.unquote_plus(str(s))
    except Exception:
        return str(s)

# Embedded Database Engine (SQLite)
import sqlite3

_db_connections: Dict[str, Any] = {}
_db_counter = 0

def fox_db_open(path=":memory:"):
    global _db_counter
    path_str = str(path)
    try:
        conn = sqlite3.connect(path_str, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        _db_counter += 1
        handle = f"db_{_db_counter}"
        _db_connections[handle] = conn
        return FoxPack({
            "handle": handle,
            "path": path_str,
            "ok": 1,
            "error": ""
        })
    except Exception as e:
        return FoxPack({
            "handle": "",
            "path": path_str,
            "ok": 0,
            "error": str(e)
        })

def _get_db_conn(target):
    if hasattr(target, "_data") and "handle" in target._data:
        return _db_connections.get(target._data["handle"])
    if isinstance(target, str) and target in _db_connections:
        return _db_connections[target]
    return None

def fox_db_execute(target, sql, params=None):
    conn = _get_db_conn(target)
    if conn is None:
        return FoxPack({"ok": 0, "rows_affected": 0, "last_id": 0, "error": "Invalid DB handle"})
    try:
        clean_params = []
        if params is not None:
            if isinstance(params, list):
                clean_params = [_clean_obj(p) for p in params]
            elif hasattr(params, "_data"):
                clean_params = _clean_obj(params)
            else:
                clean_params = [params]
        cursor = conn.cursor()
        cursor.execute(str(sql), clean_params)
        conn.commit()
        return FoxPack({
            "ok": 1,
            "rows_affected": cursor.rowcount,
            "last_id": cursor.lastrowid or 0,
            "error": ""
        })
    except Exception as e:
        return FoxPack({
            "ok": 0,
            "rows_affected": 0,
            "last_id": 0,
            "error": str(e)
        })

def fox_db_query(target, sql, params=None):
    conn = _get_db_conn(target)
    if conn is None:
        return []
    try:
        clean_params = []
        if params is not None:
            if isinstance(params, list):
                clean_params = [_clean_obj(p) for p in params]
            elif hasattr(params, "_data"):
                clean_params = _clean_obj(params)
            else:
                clean_params = [params]
        cursor = conn.cursor()
        cursor.execute(str(sql), clean_params)
        rows = cursor.fetchall()
        result = []
        for r in rows:
            row_dict = {col: r[col] for col in r.keys()}
            result.append(FoxPack(row_dict))
        return result
    except Exception:
        return []

def fox_db_close(target):
    conn = _get_db_conn(target)
    if conn is not None:
        try:
            conn.close()
            if hasattr(target, "_data") and "handle" in target._data:
                _db_connections.pop(target._data["handle"], None)
            elif isinstance(target, str):
                _db_connections.pop(target, None)
            return 1
        except Exception:
            return 0
    return 0

# Production HTTP Server & Routing Engine
_http_servers: Dict[str, Any] = {}
_server_counter = 0

class FoxHTTPRequestHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def _handle_request(self, method):
        server_obj = getattr(self.server, "_fox_server_instance", None)
        routes = server_obj.get("routes", {}) if server_obj else {}

        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)
        flat_query = {k: v[0] if len(v) == 1 else v for k, v in query.items()}

        content_length = int(self.headers.get("Content-Length", 0))
        body_bytes = self.rfile.read(content_length) if content_length > 0 else b""
        body_str = body_bytes.decode("utf-8", errors="replace")

        parsed_json = None
        try:
            parsed_json = to_fox_val(json.loads(body_str))
        except Exception:
            pass

        req_pack = FoxPack({
            "method": method,
            "path": path,
            "query": FoxPack(flat_query),
            "headers": FoxPack({k.lower(): v for k, v in self.headers.items()}),
            "body": body_str,
            "json": parsed_json if parsed_json is not None else FoxPack({})
        })

        handler = (routes.get((method, path)) or 
                   routes.get(("*", path)) or 
                   routes.get((method, "*")) or 
                   routes.get(("*", "*")))

        if handler is None:
            self.send_response(404)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"error": "Not Found", "status": 404}')
            return

        try:
            if callable(handler):
                resp_val = handler(req_pack)
            else:
                resp_val = handler
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e), "status": 500}).encode("utf-8"))
            return

        status = 200
        headers = {}
        body = b""

        if hasattr(resp_val, "_data"):
            data = resp_val._data
            status = int(data.get("status", 200))
            if "headers" in data:
                headers = _clean_obj(data["headers"])
            if "json" in data:
                body = json.dumps(_clean_obj(data["json"])).encode("utf-8")
                if "Content-Type" not in headers and "content-type" not in headers:
                    headers["Content-Type"] = "application/json"
            elif "body" in data:
                b = data["body"]
                if hasattr(b, "_data") or isinstance(b, (dict, list)):
                    body = json.dumps(_clean_obj(b)).encode("utf-8")
                    if "Content-Type" not in headers and "content-type" not in headers:
                        headers["Content-Type"] = "application/json"
                elif isinstance(b, str):
                    body = b.encode("utf-8")
                elif isinstance(b, (bytes, bytearray)):
                    body = bytes(b)
                else:
                    body = str(b).encode("utf-8")
            else:
                body = json.dumps(_clean_obj(resp_val)).encode("utf-8")
                if "Content-Type" not in headers and "content-type" not in headers:
                    headers["Content-Type"] = "application/json"
        elif isinstance(resp_val, (dict, list)):
            body = json.dumps(_clean_obj(resp_val)).encode("utf-8")
            headers["Content-Type"] = "application/json"
        elif isinstance(resp_val, str):
            body = resp_val.encode("utf-8")
            headers["Content-Type"] = "text/plain; charset=utf-8"
        elif resp_val is None:
            body = b""
        else:
            body = str(resp_val).encode("utf-8")
            headers["Content-Type"] = "text/plain; charset=utf-8"

        self.send_response(status)
        for k, v in headers.items():
            self.send_header(str(k), str(v))
        if "Content-Length" not in headers and "content-length" not in headers:
            self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        self._handle_request("GET")

    def do_POST(self):
        self._handle_request("POST")

    def do_PUT(self):
        self._handle_request("PUT")

    def do_DELETE(self):
        self._handle_request("DELETE")

    def do_PATCH(self):
        self._handle_request("PATCH")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, PATCH, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()

def fox_http_response(body=None, status=200, headers=None, json_data=None):
    resp = {"status": int(status)}
    if headers:
        resp["headers"] = headers
    if json_data is not None:
        resp["json"] = json_data
    elif body is not None:
        if hasattr(body, "_data") or isinstance(body, (dict, list)):
            resp["json"] = body
        else:
            resp["body"] = body
    return FoxPack(resp)

def fox_http_server(port=8080, host="0.0.0.0"):
    global _server_counter
    _server_counter += 1
    sid = f"srv_{_server_counter}"
    server_info = {
        "id": sid,
        "host": str(host),
        "port": int(port),
        "routes": {},
        "running": 0,
        "httpd": None,
        "thread": None
    }
    _http_servers[sid] = server_info
    return FoxPack({
        "id": sid,
        "host": str(host),
        "port": int(port),
        "ok": 1
    })

def fox_http_route(server, method, path, handler):
    sid = server["id"] if hasattr(server, "_data") else str(server)
    if sid in _http_servers:
        _http_servers[sid]["routes"][(str(method).upper(), str(path))] = handler
        return 1
    return 0

def fox_http_start(server):
    sid = server["id"] if hasattr(server, "_data") else str(server)
    if sid not in _http_servers:
        return 0
    info = _http_servers[sid]
    if info["running"]:
        return 1
    try:
        httpd = http.server.HTTPServer((info["host"], info["port"]), FoxHTTPRequestHandler)
        httpd._fox_server_instance = info
        info["port"] = httpd.server_port
        info["httpd"] = httpd
        t = threading.Thread(target=httpd.serve_forever, daemon=True)
        t.start()
        info["thread"] = t
        info["running"] = 1
        if hasattr(server, "_data"):
            server._data["port"] = httpd.server_port
            server._data["running"] = 1
        return 1
    except Exception as e:
        if hasattr(server, "_data"):
            server._data["error"] = str(e)
        return 0

def fox_http_stop(server):
    sid = server["id"] if hasattr(server, "_data") else str(server)
    if sid not in _http_servers:
        return 0
    info = _http_servers[sid]
    if info["running"] and info["httpd"]:
        try:
            info["httpd"].shutdown()
            info["running"] = 0
            if hasattr(server, "_data"):
                server._data["running"] = 0
            return 1
        except Exception:
            return 0
    return 0

# Security, Hashing & Cryptography Utilities
def fox_hash_sha256(data):
    return hashlib.sha256(str(data).encode("utf-8")).hexdigest()

def fox_hash_sha512(data):
    return hashlib.sha512(str(data).encode("utf-8")).hexdigest()

def fox_hash_md5(data):
    return hashlib.md5(str(data).encode("utf-8")).hexdigest()

def fox_hmac_sha256(key, message):
    return hmac.new(str(key).encode("utf-8"), str(message).encode("utf-8"), hashlib.sha256).hexdigest()

def fox_uuid():
    return str(uuid.uuid4())

def fox_secure_token(nbytes=32):
    return secrets.token_hex(int(nbytes))

def fox_base64_encode(data):
    return base64.b64encode(str(data).encode("utf-8")).decode("utf-8")

def fox_base64_decode(encoded_str):
    try:
        return base64.b64decode(str(encoded_str).encode("utf-8")).decode("utf-8", errors="replace")
    except Exception:
        return ""

def fox_hex_encode(data):
    return str(data).encode("utf-8").hex()

def fox_hex_decode(hex_str):
    try:
        return bytes.fromhex(str(hex_str)).decode("utf-8", errors="replace")
    except Exception:
        return ""

# System, Environment & Process Execution
def fox_get_env(key, default=""):
    return os.environ.get(str(key), str(default))

def fox_set_env(key, value):
    os.environ[str(key)] = str(value)
    return 1

def fox_list_env():
    return FoxPack(dict(os.environ))

def fox_exec_cmd(command, timeout=30.0):
    try:
        res = subprocess.run(
            str(command),
            shell=True,
            capture_output=True,
            text=True,
            timeout=float(timeout)
        )
        return FoxPack({
            "ok": 1 if res.returncode == 0 else 0,
            "exit_code": res.returncode,
            "stdout": res.stdout,
            "stderr": res.stderr
        })
    except subprocess.TimeoutExpired:
        return FoxPack({
            "ok": 0,
            "exit_code": -1,
            "stdout": "",
            "stderr": "Execution timed out"
        })
    except Exception as e:
        return FoxPack({
            "ok": 0,
            "exit_code": -1,
            "stdout": "",
            "stderr": str(e)
        })

def fox_platform():
    return sys.platform

def fox_cpu_count():
    return os.cpu_count() or 1

def fox_make_dir(path):
    try:
        os.makedirs(str(path), exist_ok=True)
        return 1
    except Exception:
        return 0

def fox_remove_dir(path):
    import shutil
    try:
        shutil.rmtree(str(path))
        return 1
    except Exception:
        return 0

def fox_abs_path(path):
    return os.path.abspath(str(path))

def fox_file_size(path):
    try:
        return os.path.getsize(str(path))
    except Exception:
        return -1

# Concurrency & Background Tasks
_task_executor = concurrent.futures.ThreadPoolExecutor(max_workers=16)

def fox_spawn(fn, *args):
    fut = _task_executor.submit(fn, *args)
    return FoxPack({
        "future": fut,
        "is_done": lambda: 1 if fut.done() else 0,
        "result": lambda timeout=None: fut.result(timeout=float(timeout) if timeout is not None else None)
    })

def fox_await_task(task, timeout=None):
    if hasattr(task, "_data") and "future" in task._data:
        fut = task._data["future"]
        to = float(timeout) if timeout is not None else None
        return fut.result(timeout=to)
    return task




# String utilities
def fox_split(s, sep=" "):
    return str(s).split(str(sep))

def fox_join(sep, lst):
    if isinstance(lst, list):
        return str(sep).join(str(x) for x in lst)
    return str(lst)

def fox_trim(s):
    return str(s).strip()

def fox_replace(s, old, new):
    return str(s).replace(str(old), str(new))

def fox_upper(s):
    return str(s).upper()

def fox_lower(s):
    return str(s).lower()

def fox_contains(s, sub):
    return 1 if str(sub) in str(s) else 0

def fox_starts_with(s, prefix):
    return 1 if str(s).startswith(str(prefix)) else 0

def fox_ends_with(s, suffix):
    return 1 if str(s).endswith(str(suffix)) else 0

# Game Math, Physics & Collisions
def fox_clamp(val, min_v, max_v):
    return max(float(min_v), min(float(val), float(max_v)))

def fox_lerp(a, b, t):
    return float(a) + (float(b) - float(a)) * float(t)

def fox_distance(x1, y1, x2, y2):
    return math.hypot(float(x2) - float(x1), float(y2) - float(y1))

def fox_rect_collides(x1, y1, w1, h1, x2, y2, w2, h2):
    return 1 if (float(x1) < float(x2) + float(w2) and
                 float(x1) + float(w1) > float(x2) and
                 float(y1) < float(y2) + float(h2) and
                 float(y1) + float(h1) > float(y2)) else 0

def fox_circle_collides(x1, y1, r1, x2, y2, r2):
    d = math.hypot(float(x2) - float(x1), float(y2) - float(y1))
    return 1 if d < (float(r1) + float(r2)) else 0

def fox_point_in_rect(px, py, rx, ry, rw, rh):
    return 1 if (float(rx) <= float(px) <= float(rx) + float(rw) and
                 float(ry) <= float(py) <= float(ry) + float(rh)) else 0

def fox_random(min_v=0, max_v=1):
    return random.uniform(float(min_v), float(max_v))

def fox_random_int(min_v, max_v):
    return random.randint(int(min_v), int(max_v))

def fox_random_choice(lst):
    if isinstance(lst, list) and len(lst) > 0:
        return random.choice(lst)
    return 0

"""
FoxVC Standard Shelf
Comprehensive utilities for Games, Math, File System, JSON, and String Processing.
"""

import math
import time
import json
import random
from typing import Dict, Any


def get_standard_shelf() -> Dict[str, Any]:
    return {
        # Collection Primitives
        "pack": fox_pack,
        "push": fox_push,
        "pop": fox_pop,
        "remove_at": fox_remove_at,
        "len": len,

        # Hardware & Raylib 2D Graphics Engine
        "openWindow": fox_open_window,
        "windowClosed": fox_window_closed,
        "closeWindow": fox_close_window,
        "startFrame": fox_start_frame,
        "endFrame": fox_end_frame,
        "drawBox": fox_draw_box,
        "drawCircle": fox_draw_circle,
        "drawLine": fox_draw_line,
        "drawText": fox_draw_text,
        "getFPS": fox_get_fps,
        "setFPS": fox_set_fps,
        "isKeyDown": fox_is_key_down,
        "isKeyPressed": fox_is_key_pressed,
        "mouseX": fox_get_mouse_x,
        "mouseY": fox_get_mouse_y,
        "mouseDown": fox_mouse_down,
        "mouseClicked": fox_mouse_clicked,

        # File System I/O
        "readFile": fox_read_file,
        "writeFile": fox_write_file,
        "appendFile": fox_append_file,
        "fileExists": fox_file_exists,
        "removeFile": fox_remove_file,
        "listDir": fox_list_dir,

        # JSON Data Serialization
        "jsonParse": fox_json_parse,
        "jsonString": fox_json_string,

        # String Utilities
        "split": fox_split,
        "join": fox_join,
        "trim": fox_trim,
        "replace": fox_replace,
        "upper": fox_upper,
        "lower": fox_lower,
        "contains": fox_contains,
        "startsWith": fox_starts_with,
        "endsWith": fox_ends_with,

        # Game Math & Collision Primitives
        "clamp": fox_clamp,
        "lerp": fox_lerp,
        "distance": fox_distance,
        "rectCollides": fox_rect_collides,
        "circleCollides": fox_circle_collides,
        "pointInRect": fox_point_in_rect,
        "random": fox_random,
        "randomInt": fox_random_int,
        "randomChoice": fox_random_choice,

        # Raw Math Primitives
        "pi": math.pi,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "sqrt": math.sqrt,
        "floor": math.floor,
        "ceil": math.ceil,
        "abs": abs,
        "round": round,

        # Clock & System
        "time": time.time,
        "sleep": time.sleep,

        # Outbound HTTP & Networking
        "httpGet": fox_http_get,
        "httpPost": fox_http_post,
        "httpPut": fox_http_put,
        "httpDelete": fox_http_delete,
        "fetch": fox_fetch,
        "urlEncode": fox_url_encode,
        "urlDecode": fox_url_decode,

        # Database Engine (Embedded SQLite)
        "dbOpen": fox_db_open,
        "dbExecute": fox_db_execute,
        "dbQuery": fox_db_query,
        "dbClose": fox_db_close,

        # Production HTTP Server & REST API Framework
        "httpServer": fox_http_server,
        "httpRoute": fox_http_route,
        "httpStart": fox_http_start,
        "httpStop": fox_http_stop,
        "httpResponse": fox_http_response,

        # Security, Cryptography & Auth
        "hashSha256": fox_hash_sha256,
        "hashSha512": fox_hash_sha512,
        "hashMd5": fox_hash_md5,
        "hmacSha256": fox_hmac_sha256,
        "uuid": fox_uuid,
        "uuid4": fox_uuid,
        "secureToken": fox_secure_token,
        "base64Encode": fox_base64_encode,
        "base64Decode": fox_base64_decode,
        "hexEncode": fox_hex_encode,
        "hexDecode": fox_hex_decode,

        # System, Environment & Process Execution
        "getEnv": fox_get_env,
        "setEnv": fox_set_env,
        "listEnv": fox_list_env,
        "execCmd": fox_exec_cmd,
        "platform": fox_platform,
        "cpuCount": fox_cpu_count,
        "makeDir": fox_make_dir,
        "removeDir": fox_remove_dir,
        "absPath": fox_abs_path,
        "fileSize": fox_file_size,

        # Concurrency & Background Tasks
        "spawn": fox_spawn,
        "awaitTask": fox_await_task,
    }
