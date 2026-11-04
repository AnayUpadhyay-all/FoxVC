"""
FoxVC Data Serialization Shelf (shelves/data.py).
Provides native parsing and serialization for JSON, CSV, TOML, and structured key-value data.
"""

import json
import csv
import io
import base64
from typing import Dict, Any, List, Optional
from .common import to_fox_val, _clean_obj, SecurityPolicy


def fox_json_parse(json_str: str) -> Any:
    try:
        val = json.loads(json_str)
        return to_fox_val(val)
    except Exception as e:
        return {"error": str(e), "ok": False}


def fox_json_stringify(obj: Any, indent: int = 0) -> str:
    try:
        clean = _clean_obj(obj)
        ind = int(indent) if indent and int(indent) > 0 else None
        return json.dumps(clean, indent=ind)
    except Exception as e:
        return f'{{"error": "{str(e)}"}}'


def fox_csv_parse(csv_text: str) -> List[List[Any]]:
    try:
        reader = csv.reader(io.StringIO(str(csv_text)))
        rows = []
        for r in reader:
            parsed_row = []
            for cell in r:
                try:
                    if "." in cell:
                        parsed_row.append(float(cell))
                    else:
                        parsed_row.append(int(cell))
                except ValueError:
                    parsed_row.append(cell)
            rows.append(parsed_row)
        return rows
    except Exception as e:
        return [[f"Error: {e}"]]


def fox_csv_stringify(rows: List[List[Any]]) -> str:
    try:
        out = io.StringIO()
        writer = csv.writer(out)
        for row in rows:
            if isinstance(row, list):
                writer.writerow([_clean_obj(c) for c in row])
        return out.getvalue()
    except Exception as e:
        return f"Error: {e}"


def fox_b64_encode(text: str) -> str:
    try:
        return base64.b64encode(str(text).encode("utf-8")).decode("utf-8")
    except Exception:
        return ""


def fox_b64_decode(b64_str: str) -> str:
    try:
        return base64.b64decode(str(b64_str).encode("utf-8")).decode("utf-8")
    except Exception:
        return ""


def fox_hex_encode(text: str) -> str:
    try:
        return str(text).encode("utf-8").hex()
    except Exception:
        return ""


def fox_hex_decode(hex_str: str) -> str:
    try:
        return bytes.fromhex(str(hex_str)).decode("utf-8")
    except Exception:
        return ""


def fox_kv_parse(text: str) -> Dict[str, Any]:
    """Parses simple INI / TOML-like key = value configuration lines."""
    result = {}
    for line in str(text).splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith(";"):
            continue
        if "=" in line:
            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            try:
                if "." in v:
                    result[k] = float(v)
                else:
                    result[k] = int(v)
            except ValueError:
                if v.lower() in ("true", "aye"):
                    result[k] = 1
                elif v.lower() in ("false", "nay"):
                    result[k] = 0
                else:
                    result[k] = v
    return result


def get_data_shelf(policy: Optional[SecurityPolicy] = None) -> Dict[str, Any]:
    return {
        "jsonParse": fox_json_parse,
        "jsonStringify": fox_json_stringify,
        "csvParse": fox_csv_parse,
        "csvStringify": fox_csv_stringify,
        "b64Encode": fox_b64_encode,
        "b64Decode": fox_b64_decode,
        "hexEncode": fox_hex_encode,
        "hexDecode": fox_hex_decode,
        "kvParse": fox_kv_parse,
    }
