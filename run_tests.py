#!/usr/bin/env python3
"""
Test runner for RSU Optimizer application.
Run this script to execute all unit tests.
"""

import sys
import os
import unittest
from pathlib import Path

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def run_tests():
    """Run all unit tests and display results."""
    print("🚀 Starting RSU Optimizer Unit Tests")
    print("=" * 60)
    
    # Discover and run tests
    loader = unittest.TestLoader()
    start_dir = os.path.dirname(os.path.abspath(__file__))
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    # Run tests with verbose output
    runner = unittest.TextTestRunner(
        verbosity=2,
        stream=sys.stdout,
        descriptions=True,
        failfast=False
    )
    
    print(f"📁 Test discovery directory: {start_dir}")
    print(f"🔍 Looking for test files: test_*.py")
    print("=" * 60)
    
    # Run the tests
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"✅ Tests run: {result.testsRun}")
    print(f"❌ Failures: {len(result.failures)}")
    print(f"⚠️  Errors: {len(result.errors)}")
    print(f"⏭️  Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    
    # Calculate success rate
    if result.testsRun > 0:
        success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun) * 100
        print(f"📈 Success rate: {success_rate:.1f}%")
    
    print("=" * 60)
    
    # Print detailed failure information
    if result.failures:
        print("\n❌ FAILURES:")
        print("-" * 40)
        for test, traceback in result.failures:
            print(f"  🔴 {test}")
            print(f"     {traceback.split('AssertionError:')[-1].strip()}")
            print()
    
    # Print detailed error information
    if result.errors:
        print("\n⚠️  ERRORS:")
        print("-" * 40)
        for test, traceback in result.errors:
            print(f"  🟡 {test}")
            print(f"     {traceback.split('Exception:')[-1].strip()}")
            print()
    
    # Return appropriate exit code
    if result.failures or result.errors:
        print("❌ Some tests failed. Please review the output above.")
        return 1
    else:
        print("✅ All tests passed successfully!")
        return 0

def run_specific_test(test_name):
    """Run a specific test by name."""
    print(f"🎯 Running specific test: {test_name}")
    print("=" * 60)
    
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromName(test_name)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return 0 if not (result.failures or result.errors) else 1

def list_tests():
    """List all available tests."""
    print("📋 Available Tests:")
    print("=" * 60)
    
    loader = unittest.TestLoader()
    start_dir = os.path.dirname(os.path.abspath(__file__))
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    for test_suite in suite:
        for test_case in test_suite:
            for test_method in test_case:
                print(f"  • {test_method}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Run RSU Optimizer unit tests')
    parser.add_argument('--test', '-t', help='Run a specific test by name')
    parser.add_argument('--list', '-l', action='store_true', help='List all available tests')
    
    args = parser.parse_args()
    
    if args.list:
        list_tests()
    elif args.test:
        exit_code = run_specific_test(args.test)
        sys.exit(exit_code)
    else:
        exit_code = run_tests()
        sys.exit(exit_code)
