"""Legacy v0.3 Test Runner for FoxVC.

This runner executes the historical v0.3 test suite preserved in tests/legacy_v0_3/.
These tests reflect an earlier stage of FoxVC (v0.3) prior to the 25-keyword language
standardization and architectural refactoring in v0.5+.

Running this suite directly documents pre-existing failures and historical regression status
without polluting standard modern test discovery (python3 -m unittest discover tests).
"""

import sys
import os
import unittest
from unittest.mock import patch
import io

def run_legacy_suite():
    legacy_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(legacy_dir, "..", ".."))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    print("=" * 70)
    print("🦊 FOXVC PRESERVED HISTORICAL v0.3 TEST SUITE RUNNER")
    print("=" * 70)
    print(f"Directory: {legacy_dir}")
    print("Note: Obsolete grammar and removed modules (spatial, web runtime) will fail as expected.")
    print("-" * 70)

    # Patch stdin to avoid hanging if an old test prompts user
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir=legacy_dir, pattern="test_*.py")
    
    with patch("sys.stdin", io.StringIO("test_input\n")):
        runner = unittest.TextTestRunner(verbosity=1)
        result = runner.run(suite)

    print("-" * 70)
    print(f"Legacy Tests Run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    print("=" * 70)
    return result

if __name__ == "__main__":
    run_legacy_suite()
