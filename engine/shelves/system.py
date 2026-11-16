"""
FoxVC System, Environment, Process Execution, and Concurrency Shelf.
Enhanced with DevOps & Container Automation Primitives (Modern Bash Alternative).
"""

import os
import sys
import time
import shutil
import subprocess
import urllib.request
import concurrent.futures
from typing import Dict, Any, Optional
from engine.runtime import FoxPack
from .common import SecurityPolicy

_task_executor = concurrent.futures.ThreadPoolExecutor(max_workers=16)


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


def fox_exec_output(command, timeout=30.0) -> str:
    """Run a shell command and return its trimmed stdout directly (DevOps convenience)."""
    res = fox_exec_cmd(command, timeout=timeout)
    return res["stdout"].strip() if res["ok"] else ""


def fox_disk_usage(path: str = "/") -> FoxPack:
    """Return disk storage stats: total_gb, used_gb, free_gb, percent_used."""
    try:
        target = os.path.abspath(str(path))
        usage = shutil.disk_usage(target)
        gb = 1024 ** 3
        total = usage.total / gb
        used = usage.used / gb
        free = usage.free / gb
        pct = (usage.used / usage.total) * 100 if usage.total > 0 else 0
        return FoxPack({
            "total_gb": round(total, 2),
            "used_gb": round(used, 2),
            "free_gb": round(free, 2),
            "percent": round(pct, 1)
        })
    except Exception as e:
        return FoxPack({"total_gb": 0.0, "used_gb": 0.0, "free_gb": 0.0, "percent": 0.0, "error": str(e)})


def fox_memory_usage() -> FoxPack:
    """Return system RAM usage stats (Linux/Unix)."""
    try:
        if os.path.exists("/proc/meminfo"):
            mem = {}
            with open("/proc/meminfo", "r") as f:
                for line in f:
                    parts = line.split(":")
                    if len(parts) == 2:
                        key = parts[0].strip()
                        val = parts[1].strip().split()[0]
                        if val.isdigit():
                            mem[key] = int(val)
            total_kb = mem.get("MemTotal", 0)
            avail_kb = mem.get("MemAvailable", mem.get("MemFree", 0))
            used_kb = total_kb - avail_kb
            mb = 1024
            pct = (used_kb / total_kb) * 100 if total_kb > 0 else 0
            return FoxPack({
                "total_mb": round(total_kb / mb, 1),
                "used_mb": round(used_kb / mb, 1),
                "free_mb": round(avail_kb / mb, 1),
                "percent": round(pct, 1)
            })
    except Exception:
        pass
    return FoxPack({"total_mb": 0.0, "used_mb": 0.0, "free_mb": 0.0, "percent": 0.0})


def fox_which(binary_name: Any) -> str:
    """Return the absolute path to a binary or empty string if not found."""
    return shutil.which(str(binary_name)) or ""


def fox_http_ping(url: Any, timeout: float = 3.0) -> int:
    """Return 1 if the target HTTP/HTTPS endpoint returns status < 400, else 0."""
    try:
        req = urllib.request.Request(str(url), headers={"User-Agent": "FoxVC-Healthcheck/1.0"})
        with urllib.request.urlopen(req, timeout=float(timeout)) as res:
            return 1 if res.status < 400 else 0
    except Exception:
        return 0


def fox_is_process_running(proc_name: Any) -> int:
    """Check if any process matching name is currently running."""
    name = str(proc_name).strip()
    try:
        res = subprocess.run(["pgrep", "-f", name], capture_output=True, text=True)
        return 1 if res.returncode == 0 and res.stdout.strip() else 0
    except Exception:
        return 0


def fox_platform():
    return sys.platform


def fox_cpu_count():
    return os.cpu_count() or 1


MAX_CONCURRENT_TASKS = 64
_active_futures = set()

def fox_spawn(fn, *args):
    global _active_futures
    _active_futures = {f for f in _active_futures if not f.done()}
    if len(_active_futures) >= MAX_CONCURRENT_TASKS:
        raise RuntimeError(f"ResourceLimitExceeded: Cannot spawn background task, maximum concurrent limit ({MAX_CONCURRENT_TASKS}) reached")

    fut = _task_executor.submit(fn, *args)
    _active_futures.add(fut)
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


def get_system_shelf(policy: Optional[SecurityPolicy] = None) -> Dict[str, Any]:
    if policy is None:
        policy = SecurityPolicy()

    def _get_env(key, default=""):
        if policy.sandboxed:
            return policy.isolated_env.get(str(key), str(default))
        return fox_get_env(key, default)

    def _set_env(key, value):
        if policy.sandboxed:
            policy.isolated_env[str(key)] = str(value)
            return 1
        return fox_set_env(key, value)

    def _list_env():
        if policy.sandboxed:
            return FoxPack(dict(policy.isolated_env))
        return fox_list_env()

    def _exec_cmd(command, timeout=30.0):
        if policy.sandboxed:
            return FoxPack({
                "ok": 0,
                "exit_code": -1,
                "stdout": "",
                "stderr": "PermissionDenied: Subprocess execution is disabled in sandboxed context"
            })
        return fox_exec_cmd(command, timeout)

    def _exec_output(command, timeout=30.0):
        if policy.sandboxed:
            return ""
        return fox_exec_output(command, timeout)

    def _disk_usage(path="/"):
        return fox_disk_usage(path)

    def _memory_usage():
        return fox_memory_usage()

    def _which(binary_name):
        return fox_which(binary_name)

    def _http_ping(url, timeout=3.0):
        return fox_http_ping(url, timeout)

    def _is_process_running(proc_name):
        return fox_is_process_running(proc_name)

    return {
        "getEnv": _get_env,
        "setEnv": _set_env,
        "listEnv": _list_env,
        "execCmd": _exec_cmd,
        "exec": _exec_output,
        "execOutput": _exec_output,
        "diskUsage": _disk_usage,
        "memoryUsage": _memory_usage,
        "which": _which,
        "httpPing": _http_ping,
        "isProcessRunning": _is_process_running,
        "platform": fox_platform,
        "cpuCount": fox_cpu_count,
        "time": time.time,
        "sleep": time.sleep,
        "spawn": fox_spawn,
        "awaitTask": fox_await_task,
    }
