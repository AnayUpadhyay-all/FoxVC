"""
FoxVC System, Environment, Process Execution, and Concurrency Shelf.
"""

import os
import sys
import time
import subprocess
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

    return {
        "getEnv": _get_env,
        "setEnv": _set_env,
        "listEnv": _list_env,
        "execCmd": _exec_cmd,
        "platform": fox_platform,
        "cpuCount": fox_cpu_count,
        "time": time.time,
        "sleep": time.sleep,
        "spawn": fox_spawn,
        "awaitTask": fox_await_task,
    }
