#!/usr/bin/env python3
"""Simple test runner for carbon provider tests."""

import sys
import subprocess

if __name__ == "__main__":
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_carbon_provider.py", "-v", "--tb=short"],
        cwd="d:\\ecopilot",
        capture_output=False,
        text=True
    )
    sys.exit(result.returncode)
