#!/usr/bin/env python3
"""Standalone test runner for event_app.

Usage:
    python test_app.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import TestEvent, TestEventStore
import unittest

if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestEvent))
    suite.addTests(loader.loadTestsFromTestCase(TestEventStore))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
