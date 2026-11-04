"""
FoxVC Language Server Protocol (LSP) Server (foxvc lsp)
Implements standard JSON-RPC 2.0 over stdin/stdout for VS Code, Cursor,
and Neovim autocompletion, real-time diagnostic squigglies, and hover documentation.
"""

import sys
import os
import json
import re
from typing import Dict, Any, List, Optional

from engine.lexer import Lexer
from engine.parser import Parser
from engine.linter import FoxLinter
import engine.runtime as rt

FOX_KEYWORDS_DOCS = {
    "lock": "Immutable variable declaration: `lock x = 10`. Cannot be reassigned.",
    "shift": "Mutable variable declaration: `shift counter = 0`. Can be updated.",
    "blank": "Null/None literal value.",
    "act": "Subroutine / function declaration: `act name(params) { ... }`.",
    "emit": "Return a value or export from a function/module: `emit result`.",
    "pick": "Conditional decision statement: `pick (cond) { alt val: ... otherwise: ... }`.",
    "alt": "Branch alternative matching condition or value.",
    "otherwise": "Fallback branch in conditional or error trap blocks.",
    "spin": "Conditional loop: `spin (cond) { ... }`.",
    "cycle": "Counted range iteration loop: `cycle (i in 0..10) { ... }`.",
    "pulse": "Continuous delta-time loop for real-time game/animation engines.",
    "halt": "Breaks out of the innermost loop.",
    "skip": "Skips to the next iteration of the loop.",
    "say": "Standard output print function: `say 'message'`.",
    "ask": "Standard input prompt: `lock name = ask('Your name: ')`.",
    "guard": "Defensive assertion: `guard (x > 0) otherwise { ... }`.",
    "trap": "Exception catcher and isolation block.",
    "fuse": "Module import statement: `fuse net`, `fuse 'path/to/module'`.",
    "pack": "Dynamic array collection: `pack [1, 2, 3]`.",
    "mold": "Object blueprint/type schema definition.",
    "aye": "Boolean literal `true`.",
    "nay": "Boolean literal `false`.",
    "also": "Logical AND with short-circuit evaluation: `a also b`.",
    "either": "Logical OR with short-circuit evaluation: `a either b`.",
    "deny": "Logical NOT unary negation: `deny is_open`."
}

SHELVES_DOCS = {
    "net": "Network microservices, HTTP client/server, and socket bindings.",
    "math": "Trigonometric and mathematical algorithms (sin, cos, sqrt, pow).",
    "file": "File system I/O, directory traversal, and persistent storage.",
    "crypto": "Hashing algorithms (SHA-256, MD5, base64 encoding).",
    "db": "Embedded SQLite database queries and transactions.",
    "graphics": "Hardware-accelerated 2D drawing and window canvas via Raylib.",
    "system": "OS interaction, environment variables, time, and subprocesses.",
    "data": "Data serialization and parsing for JSON, CSV, TOML, and YAML.",
    "audio": "Audio playback, streaming, and sound synthesis.",
    "socket": "Raw asynchronous TCP and WebSocket networking."
}


class FoxLanguageServer:
    """JSON-RPC 2.0 Language Server implementation for FoxVC."""

    def __init__(self):
        self.documents: Dict[str, str] = {}
        self.linter = FoxLinter()

    def handle_request(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        method = message.get("method")
        msg_id = message.get("id")
        params = message.get("params", {})

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "capabilities": {
                        "textDocumentSync": 1,  # Full sync
                        "completionProvider": {
                            "resolveProvider": False,
                            "triggerCharacters": [".", " "]
                        },
                        "hoverProvider": True
                    },
                    "serverInfo": {
                        "name": "foxvc-lsp",
                        "version": f"v{rt.FOXVC_ENGINE_VERSION}"
                    }
                }
            }

        elif method == "initialized":
            return None

        elif method == "textDocument/didOpen":
            doc = params.get("textDocument", {})
            uri = doc.get("uri", "")
            text = doc.get("text", "")
            self.documents[uri] = text
            self._publish_diagnostics(uri, text)
            return None

        elif method == "textDocument/didChange":
            doc = params.get("textDocument", {})
            uri = doc.get("uri", "")
            changes = params.get("contentChanges", [])
            if changes:
                text = changes[-1].get("text", "")
                self.documents[uri] = text
                self._publish_diagnostics(uri, text)
            return None

        elif method == "textDocument/didClose":
            uri = params.get("textDocument", {}).get("uri", "")
            if uri in self.documents:
                del self.documents[uri]
            return None

        elif method == "textDocument/completion":
            items = []
            # Keywords
            for kw, doc in FOX_KEYWORDS_DOCS.items():
                items.append({
                    "label": kw,
                    "kind": 14,  # Keyword
                    "detail": f"FoxVC Keyword: {kw}",
                    "documentation": doc
                })
            # Shelves
            for sh, doc in SHELVES_DOCS.items():
                items.append({
                    "label": sh,
                    "kind": 9,  # Module
                    "detail": f"FoxVC Standard Shelf: {sh}",
                    "documentation": doc
                })
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": items
            }

        elif method == "textDocument/hover":
            pos = params.get("position", {})
            uri = params.get("textDocument", {}).get("uri", "")
            text = self.documents.get(uri, "")
            word = self._extract_word_at_pos(text, pos.get("line", 0), pos.get("character", 0))

            if word in FOX_KEYWORDS_DOCS:
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "contents": {
                            "kind": "markdown",
                            "value": f"**FoxVC Keyword: `{word}`**\n\n{FOX_KEYWORDS_DOCS[word]}"
                        }
                    }
                }
            elif word in SHELVES_DOCS:
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "contents": {
                            "kind": "markdown",
                            "value": f"**FoxVC Shelf: `{word}`**\n\n{SHELVES_DOCS[word]}"
                        }
                    }
                }
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": None
            }

        elif method == "shutdown":
            return {"jsonrpc": "2.0", "id": msg_id, "result": None}

        elif method == "exit":
            sys.exit(0)

        if msg_id is not None:
            return {"jsonrpc": "2.0", "id": msg_id, "result": None}
        return None

    def _extract_word_at_pos(self, text: str, line_no: int, char_no: int) -> str:
        lines = text.splitlines()
        if line_no >= len(lines):
            return ""
        line = lines[line_no]
        if char_no >= len(line):
            char_no = len(line) - 1

        start = char_no
        while start > 0 and (line[start - 1].isalnum() or line[start - 1] == "_"):
            start -= 1

        end = char_no
        while end < len(line) and (line[end].isalnum() or line[end] == "_"):
            end += 1

        return line[start:end]

    def _publish_diagnostics(self, uri: str, text: str):
        diagnostics = []
        messages = self.linter.lint_source(text)

        for m in messages:
            line_idx = max(0, m.line - 1)
            col_idx = max(0, m.col - 1)
            severity = 1 if m.severity == "error" else 2  # 1: Error, 2: Warning

            diagnostics.append({
                "range": {
                    "start": {"line": line_idx, "character": col_idx},
                    "end": {"line": line_idx, "character": col_idx + 10}
                },
                "severity": severity,
                "code": m.code,
                "source": "foxvc",
                "message": m.message
            })

        notification = {
            "jsonrpc": "2.0",
            "method": "textDocument/publishDiagnostics",
            "params": {
                "uri": uri,
                "diagnostics": diagnostics
            }
        }
        self._send_response(notification)

    def _send_response(self, response: Dict[str, Any]):
        body = json.dumps(response)
        header = f"Content-Length: {len(body.encode('utf-8'))}\r\n\r\n"
        sys.stdout.buffer.write((header + body).encode("utf-8"))
        sys.stdout.buffer.flush()

    def run(self):
        """Standard input listening loop parsing HTTP-like Content-Length headers."""
        while True:
            header_bytes = b""
            while b"\r\n\r\n" not in header_bytes:
                chunk = sys.stdin.buffer.read(1)
                if not chunk:
                    return
                header_bytes += chunk

            header_str = header_bytes.decode("latin1")
            content_length = 0
            for h in header_str.split("\r\n"):
                if h.lower().startswith("content-length:"):
                    content_length = int(h.split(":")[1].strip())

            body_bytes = sys.stdin.buffer.read(content_length)
            if not body_bytes:
                return

            try:
                message = json.loads(body_bytes.decode("utf-8"))
                resp = self.handle_request(message)
                if resp is not None:
                    self._send_response(resp)
            except Exception as e:
                pass


def lsp_cli(args: List[str]) -> int:
    """CLI entrypoint for `foxvc lsp`."""
    server = FoxLanguageServer()
    server.run()
    return 0
