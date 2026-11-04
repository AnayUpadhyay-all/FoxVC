"""
FoxVC Embedded Database Shelf (SQLite).
Provides zero-configuration relational persistence, parameterized queries, and sandbox confinement.
"""

import sqlite3
import re
from typing import Dict, Any, List, Optional
from engine.runtime import FoxPack
from .common import _clean_obj, SecurityPolicy

_db_connections: Dict[str, Any] = {}
_db_counter = 0


def fox_db_open(path=":memory:", uri=False):
    global _db_counter
    path_str = str(path)
    try:
        conn = sqlite3.connect(path_str, check_same_thread=False, uri=uri)
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


def fox_db_execute(target, sql, params=None, policy: Optional[SecurityPolicy] = None):
    conn = _get_db_conn(target)
    if conn is None:
        return FoxPack({"ok": 0, "rows_affected": 0, "last_id": 0, "error": "Invalid DB handle"})

    sql_str = str(sql)
    if policy and policy.sandboxed:
        # Prevent ATTACH DATABASE or arbitrary file operations via SQL
        if re.search(r"\bATTACH\s+DATABASE\b", sql_str, re.IGNORECASE):
            return FoxPack({"ok": 0, "rows_affected": 0, "last_id": 0, "error": "PermissionDenied: ATTACH DATABASE is blocked in sandboxed mode"})

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
        cursor.execute(sql_str, clean_params)
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


def get_db_shelf(policy: Optional[SecurityPolicy] = None) -> Dict[str, Any]:
    if policy is None:
        policy = SecurityPolicy()

    def _db_open(path=":memory:"):
        path_str = str(path)
        if policy.sandboxed and path_str != ":memory:":
            target = policy.resolve_path(path_str)
            if target is None:
                return FoxPack({
                    "handle": "",
                    "path": path_str,
                    "ok": 0,
                    "error": "PermissionDenied: Database path outside sandbox"
                })
            path_str = target
        return fox_db_open(path_str, uri=False)

    def _db_execute(target, sql, params=None):
        return fox_db_execute(target, sql, params=params, policy=policy)

    return {
        "dbOpen": _db_open,
        "dbExecute": _db_execute,
        "dbQuery": fox_db_query,
        "dbClose": fox_db_close,
    }
