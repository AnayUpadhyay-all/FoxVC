"""
FoxVC Outbound Networking and HTTP Server Shelf.
Provides REST client primitives, URL encoding, and the lightweight in-memory HTTP web server.
"""

import http.server
import json
import socket
import ipaddress
import ssl
import threading
import urllib.request
import urllib.error
import urllib.parse
from typing import Dict, Any, Optional

from engine.runtime import FoxPack
from .common import to_fox_val, _clean_obj, SecurityPolicy

_http_servers: Dict[str, Any] = {}
_server_counter = 0


def _is_private_or_loopback_host(host: str) -> bool:
    """Check if host resolves to loopback or private RFC 1918 / link-local IP."""
    clean_host = host.split(":")[0].strip().lower()
    if clean_host in ("localhost", "127.0.0.1", "::1", "0.0.0.0"):
        return True
    try:
        ip = ipaddress.ip_address(clean_host)
        return ip.is_loopback or ip.is_private or ip.is_link_local
    except ValueError:
        # Hostname - try to resolve
        try:
            addr_info = socket.getaddrinfo(clean_host, None)
            for item in addr_info:
                ip_str = item[4][0]
                ip = ipaddress.ip_address(ip_str)
                if ip.is_loopback or ip.is_private or ip.is_link_local:
                    return True
        except Exception:
            pass
    return False


def fox_http_request(url, method="GET", body=None, headers=None, timeout=10.0, policy: Optional[SecurityPolicy] = None):
    url_str = str(url)
    method_str = str(method).upper()
    req_headers = {}

    # Sandbox network isolation check
    if policy and policy.sandboxed:
        parsed_url = urllib.parse.urlparse(url_str)
        hostname = parsed_url.hostname or ""
        if _is_private_or_loopback_host(hostname):
            return FoxPack({
                "status": 0,
                "ok": 0,
                "body": "",
                "headers": FoxPack({}),
                "json": FoxPack({}),
                "error": "PermissionDenied: Access to loopback or private network services is blocked in sandboxed mode"
            })

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
        req_headers["User-Agent"] = "FoxVC/1.0 (NetworkingEngine)"

    try:
        req = urllib.request.Request(url_str, data=data_bytes, headers=req_headers, method=method_str)
        
        # Proper TLS Verification Context
        ctx = ssl.create_default_context()

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


def fox_http_get(url, headers=None, timeout=10.0, policy=None):
    return fox_http_request(url, method="GET", headers=headers, timeout=timeout, policy=policy)


def fox_http_post(url, body=None, headers=None, timeout=10.0, policy=None):
    return fox_http_request(url, method="POST", body=body, headers=headers, timeout=timeout, policy=policy)


def fox_http_put(url, body=None, headers=None, timeout=10.0, policy=None):
    return fox_http_request(url, method="PUT", body=body, headers=headers, timeout=timeout, policy=policy)


def fox_http_delete(url, headers=None, timeout=10.0, policy=None):
    return fox_http_request(url, method="DELETE", headers=headers, timeout=timeout, policy=policy)


def fox_fetch(url, options=None, policy=None):
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
    return fox_http_request(url, method=method, body=body, headers=headers, timeout=timeout, policy=policy)


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
                raw_headers = _clean_obj(data["headers"])
                headers = {}
                for hk, hv in raw_headers.items():
                    if hk.lower() == "content_type":
                        headers["Content-Type"] = hv
                    else:
                        headers[hk] = hv
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

    def do_GET(self): self._handle_request("GET")
    def do_POST(self): self._handle_request("POST")
    def do_PUT(self): self._handle_request("PUT")
    def do_DELETE(self): self._handle_request("DELETE")
    def do_PATCH(self): self._handle_request("PATCH")
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


def get_net_shelf(policy: Optional[SecurityPolicy] = None) -> Dict[str, Any]:
    if policy is None:
        policy = SecurityPolicy()

    def _http_get(url, headers=None, timeout=10.0):
        return fox_http_get(url, headers=headers, timeout=timeout, policy=policy)

    def _http_post(url, body=None, headers=None, timeout=10.0):
        return fox_http_post(url, body=body, headers=headers, timeout=timeout, policy=policy)

    def _http_put(url, body=None, headers=None, timeout=10.0):
        return fox_http_put(url, body=body, headers=headers, timeout=timeout, policy=policy)

    def _http_delete(url, headers=None, timeout=10.0):
        return fox_http_delete(url, headers=headers, timeout=timeout, policy=policy)

    def _fetch(url, options=None):
        return fox_fetch(url, options=options, policy=policy)

    def _http_server(port=8080, host="0.0.0.0"):
        if policy.sandboxed:
            return FoxPack({
                "id": "",
                "host": str(host),
                "port": int(port),
                "ok": 0,
                "error": "PermissionDenied: HTTP server cannot be spawned in sandboxed context"
            })
        return fox_http_server(port, host)

    return {
        "httpGet": _http_get,
        "httpPost": _http_post,
        "httpPut": _http_put,
        "httpDelete": _http_delete,
        "fetch": _fetch,
        "urlEncode": fox_url_encode,
        "urlDecode": fox_url_decode,
        "httpServer": _http_server,
        "httpRoute": fox_http_route,
        "httpStart": fox_http_start,
        "httpStop": fox_http_stop,
        "httpResponse": fox_http_response,
    }
