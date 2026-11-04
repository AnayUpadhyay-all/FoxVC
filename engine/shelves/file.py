"""
FoxVC Filesystem, JSON Data, and String Processing Shelf.
"""

import os
import json
import shutil
from typing import Dict, Any, List, Optional
from engine.runtime import FoxPack
from .common import to_fox_val, _clean_obj, SecurityPolicy


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


def fox_make_dir(path):
    try:
        os.makedirs(str(path), exist_ok=True)
        return 1
    except Exception:
        return 0


def fox_remove_dir(path):
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


# JSON Serialization
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


# String Utilities
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


def get_file_shelf(policy: Optional[SecurityPolicy] = None) -> Dict[str, Any]:
    if policy is None:
        policy = SecurityPolicy()

    def _read_file(path):
        target = policy.resolve_path(path)
        if target is None:
            return ""
        return fox_read_file(target)

    def _write_file(path, content):
        target = policy.resolve_path(path)
        if target is None:
            return 0
        return fox_write_file(target, content)

    def _append_file(path, content):
        target = policy.resolve_path(path)
        if target is None:
            return 0
        return fox_append_file(target, content)

    def _file_exists(path):
        target = policy.resolve_path(path)
        if target is None:
            return 0
        return fox_file_exists(target)

    def _remove_file(path):
        target = policy.resolve_path(path)
        if target is None:
            return 0
        return fox_remove_file(target)

    def _list_dir(path="."):
        target = policy.resolve_path(path)
        if target is None:
            return []
        return fox_list_dir(target)

    def _make_dir(path):
        target = policy.resolve_path(path)
        if target is None:
            return 0
        return fox_make_dir(target)

    def _remove_dir(path):
        target = policy.resolve_path(path)
        if target is None:
            return 0
        # Prevent removing the root sandbox directory itself
        if policy.sandboxed and policy.allowed_dir and target == policy.allowed_dir:
            return 0
        return fox_remove_dir(target)

    return {
        "readFile": _read_file,
        "writeFile": _write_file,
        "appendFile": _append_file,
        "fileExists": _file_exists,
        "removeFile": _remove_file,
        "listDir": _list_dir,
        "makeDir": _make_dir,
        "removeDir": _remove_dir,
        "absPath": fox_abs_path,
        "fileSize": fox_file_size,
        "jsonParse": fox_json_parse,
        "jsonString": fox_json_string,
        "split": fox_split,
        "join": fox_join,
        "trim": fox_trim,
        "replace": fox_replace,
        "upper": fox_upper,
        "lower": fox_lower,
        "contains": fox_contains,
        "startsWith": fox_starts_with,
        "endsWith": fox_ends_with,
    }
