#!/usr/bin/env python3
"""
Test runner for AI Marksheet Extraction API
"""

import subprocess
import sys
import os

def run_tests():
    """Run all unit tests"""
    print("🧪 Running AI Marksheet Extraction API Tests")
    print("=" * 50)
    
    try:
        # Run pytest with verbose output
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "test_marksheet_extraction.py", 
            "-v", 
            "--tb=short",
            "--color=yes"
        ], capture_output=False)
        
        if result.returncode == 0:
            print("\n✅ All tests passed!")
            return True
        else:
            print("\n❌ Some tests failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False

def run_specific_test(test_name):
    """Run a specific test"""
    print(f"🧪 Running test: {test_name}")
    print("=" * 30)
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            f"test_marksheet_extraction.py::{test_name}",
            "-v",
            "--tb=short"
        ], capture_output=False)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Error running test: {e}")
        return False

def main():
    """Main test runner"""
    if len(sys.argv) > 1:
        test_name = sys.argv[1]
        success = run_specific_test(test_name)
    else:
        success = run_tests()
    
    if success:
        print("\n🎉 Test execution completed successfully!")
        sys.exit(0)
    else:
        print("\n💥 Test execution failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
