#!/usr/bin/env python3
import unittest
import sys
import os

# Add the parent directory to the Python path so we can import the main package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def run_tests():
    """Run all test cases and return True if all tests pass, False otherwise."""
    # Discover and run tests
    loader = unittest.TestLoader()
    start_dir = os.path.dirname(os.path.abspath(__file__))
    suite = loader.discover(start_dir, pattern="test_*.py")
    
    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == '__main__':
    # Exit with non-zero status if any tests fail
    success = run_tests()
    sys.exit(0 if success else 1)
