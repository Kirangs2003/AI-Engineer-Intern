#!/usr/bin/env python3
"""
Test script for the API endpoints
"""

import requests
import json
import os
import time

def test_health_endpoint(base_url="http://localhost:8000"):
    """Test the health endpoint"""
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            data = response.json()
            print("✅ Health endpoint working")
            print(f"   Status: {data.get('status')}")
            print(f"   Gemini API configured: {data.get('gemini_api_configured')}")
            return True
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API server. Make sure it's running.")
        return False
    except Exception as e:
        print(f"❌ Health endpoint error: {e}")
        return False

def test_root_endpoint(base_url="http://localhost:8000"):
    """Test the root endpoint"""
    try:
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            data = response.json()
            print("✅ Root endpoint working")
            print(f"   Message: {data.get('message')}")
            return True
        else:
            print(f"❌ Root endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Root endpoint error: {e}")
        return False

def test_extract_endpoint_without_file(base_url="http://localhost:8000"):
    """Test extract endpoint without file (should return error)"""
    try:
        response = requests.post(f"{base_url}/extract")
        if response.status_code == 422:  # Validation error expected
            print("✅ Extract endpoint validation working (correctly rejects empty request)")
            return True
        else:
            print(f"❌ Extract endpoint unexpected response: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Extract endpoint error: {e}")
        return False

def main():
    print("API Testing")
    print("=" * 30)
    
    base_url = "http://localhost:8000"
    
    # Test endpoints
    print("Testing API endpoints...")
    
    health_ok = test_health_endpoint(base_url)
    root_ok = test_root_endpoint(base_url)
    extract_ok = test_extract_endpoint_without_file(base_url)
    
    print("\n" + "=" * 30)
    
    if health_ok and root_ok and extract_ok:
        print("✅ All API tests passed!")
        print("\nThe API is working correctly.")
        print("You can now:")
        print("1. Visit http://localhost:8000/docs for API documentation")
        print("2. Use the Streamlit UI: python run_streamlit.py")
        print("3. Upload marksheet files via the API")
    else:
        print("❌ Some API tests failed.")
        print("Make sure the API server is running: python run_api.py")

if __name__ == "__main__":
    main()
