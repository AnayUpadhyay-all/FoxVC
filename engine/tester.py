"""
FoxVC Native Test Runner (foxvc test)
Discovers and executes .fox unit test suites natively with sub-millisecond
execution timing and colored diagnostic assertions.
"""

import os
import sys
import time
import re
from dataclasses import dataclass
from typing import List, Optional, Tuple

from engine.lexer import Lexer
from engine.parser import Parser
from engine.runner import run_foxvc


@dataclass
class TestCaseResult:
    suite_path: str
    test_name: str
    passed: bool
    duration_ms: float
    error_message: Optional[str] = None
    output: Optional[str] = None


class FoxTestRunner:
    """Discovers and runs FoxVC test cases natively."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose

    def discover_test_files(self, search_path: str = ".") -> List[str]:
        """Finds all .fox files in test directories or matching test patterns."""
        test_files = []

        if os.path.isfile(search_path) and search_path.endswith(".fox"):
            return [os.path.abspath(search_path)]

        for root, _, files in os.walk(search_path):
            if "venv" in root or ".git" in root or "__pycache__" in root:
                continue
            for f in files:
                if f.endswith(".fox") and ("test" in f.lower() or "tests" in root.lower()):
                    test_files.append(os.path.abspath(os.path.join(root, f)))

        return sorted(test_files)

    def discover_test_functions(self, code: str) -> List[str]:
        """Finds all function declarations starting with test_."""
        # Matches: act test_something(...)
        pattern = r"\bact\s+(test_[a-zA-Z0-9_]*)\s*\("
        return re.findall(pattern, code)

    def run_file_suite(self, filepath: str) -> List[TestCaseResult]:
        """Runs all tests inside a single .fox file."""
        results = []
        with open(filepath, "r", encoding="utf-8") as f:
            code = f.read()

        test_funcs = self.discover_test_functions(code)

        if not test_funcs:
            # Execute entire file as a standalone integration test
            t0 = time.perf_counter()
            res = run_foxvc(code, file_path=filepath)
            elapsed_ms = (time.perf_counter() - t0) * 1000.0

            passed = res.success
            err_msg = res.error if not passed else None
            results.append(TestCaseResult(
                suite_path=filepath,
                test_name="<suite_main>",
                passed=passed,
                duration_ms=elapsed_ms,
                error_message=err_msg,
                output=res.output
            ))
            return results

        # Execute each individual test function
        for fn_name in test_funcs:
            # Append invocation of this specific test function
            harness = f"\n\n# Native Test Harness Invocation\nlock __test_res = {fn_name}()\npick __test_res == nay\n    say \"__TEST_ASSERTION_FAILED__\"\n"

            test_code = code + harness
            t0 = time.perf_counter()
            res = run_foxvc(test_code, file_path=filepath)
            elapsed_ms = (time.perf_counter() - t0) * 1000.0

            passed = res.success and ("__TEST_ASSERTION_FAILED__" not in (res.output or ""))
            err_msg = None
            if not res.success:
                err_msg = res.error
            elif not passed:
                err_msg = "Test returned 'nay' (Assertion Failure)"

            results.append(TestCaseResult(
                suite_path=filepath,
                test_name=fn_name,
                passed=passed,
                duration_ms=elapsed_ms,
                error_message=err_msg,
                output=res.output
            ))

        return results

    def run_all(self, target_path: str = ".") -> Tuple[List[TestCaseResult], int, int]:
        files = self.discover_test_files(target_path)
        all_results = []
        passed_count = 0
        failed_count = 0

        for f in files:
            file_results = self.run_file_suite(f)
            for r in file_results:
                all_results.append(r)
                if r.passed:
                    passed_count += 1
                else:
                    failed_count += 1

        return all_results, passed_count, failed_count


def test_cli(args: List[str]) -> int:
    """CLI entrypoint for `foxvc test`."""
    target = "."
    verbose = "-v" in args or "--verbose" in args

    for a in args:
        if not a.startswith("-"):
            target = a
            break

    runner = FoxTestRunner(verbose=verbose)
    files = runner.discover_test_files(target)

    print("🦊 FoxVC Native Test Runner")
    print(f"Scanning target: '{target}' ({len(files)} test files found)\n")

    if not files:
        print("No .fox test files discovered.")
        return 0

    t_start = time.perf_counter()
    all_results, passed_c, failed_c = runner.run_all(target)
    total_elapsed = (time.perf_counter() - t_start) * 1000.0

    current_suite = ""
    for r in all_results:
        rel_suite = os.path.relpath(r.suite_path)
        if rel_suite != current_suite:
            current_suite = rel_suite
            print(f"Suite: \033[1m{current_suite}\033[0m")

        if r.passed:
            badge = "\033[92m✓ PASS\033[0m"
            print(f"  {badge}  {r.test_name} \033[90m({r.duration_ms:.2f}ms)\033[0m")
        else:
            badge = "\033[91m✗ FAIL\033[0m"
            print(f"  {badge}  {r.test_name} \033[90m({r.duration_ms:.2f}ms)\033[0m")
            if r.error_message:
                print(f"        \033[91m↳ {r.error_message}\033[0m")

    print("\n" + "=" * 50)
    summary_color = "\033[92m" if failed_c == 0 else "\033[91m"
    print(f"{summary_color}Results: {passed_c} Passed | {failed_c} Failed | {len(all_results)} Total ({total_elapsed:.2f}ms)\033[0m")
    print("=" * 50)

    return 0 if failed_c == 0 else 1
