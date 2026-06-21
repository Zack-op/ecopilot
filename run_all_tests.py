#!/usr/bin/env python3
"""Run pytest and report results."""

import subprocess
import sys
import os

os.chdir('d:\\ecopilot')

result = subprocess.run(
    [sys.executable, '-m', 'pytest', 'tests/', '-v', '--tb=short'],
    capture_output=True,
    text=True
)

print(result.stdout)
print(result.stderr)
sys.exit(result.returncode)
