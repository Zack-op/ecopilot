#!/usr/bin/env python3
"""Quick syntax checker."""

import sys
import py_compile

files_to_check = [
    "d:\\ecopilot\\core\\carbon_provider.py",
    "d:\\ecopilot\\core\\telemetry_parser.py",
    "d:\\ecopilot\\tests\\test_carbon_provider.py",
]

print("=" * 60)
print("SYNTAX VALIDATION")
print("=" * 60)

all_ok = True
for filepath in files_to_check:
    try:
        py_compile.compile(filepath, doraise=True)
        print(f"✓ {filepath}")
    except py_compile.PyCompileError as e:
        print(f"✗ {filepath}")
        print(f"  Error: {e}")
        all_ok = False

if all_ok:
    print("\n✓ All files have valid Python syntax!")
else:
    print("\n✗ Some files have syntax errors!")
    sys.exit(1)
