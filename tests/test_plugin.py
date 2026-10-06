#!/usr/bin/env python3
"""Run all deterministic and integration SWT Plugin tests."""
from pathlib import Path
import unittest

TEST_ROOT = Path(__file__).resolve().parent

if __name__ == "__main__":
    suite = unittest.defaultTestLoader.discover(str(TEST_ROOT), pattern="test_*.py")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(not result.wasSuccessful())
