#!/usr/bin/env python
"""
Simple test script for authentication endpoints
Run this after starting the server with: uvicorn app.main:app --reload
"""

import requests
import json

BASE_URL = "http://localhost:8000"


def test_register():
    """Test user registration"""
    print("\n=== Testing Registration ===")
    url = f"{BASE_URL}/api/v1/auth/register"
    data = {
        "email": "test@example.com",
        "password": "testpass123",
        "name": "Test User",
        "company_name": "Test Company"
    }

    response = requests.post(url, json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    return response.status_code == 201


def test_login():
    """Test user login"""
    print("\n=== Testing Login ===")
    url = f"{BASE_URL}/api/v1/auth/login"
    data = {
        "username": "test@example.com",  # OAuth2 form uses 'username'
        "password": "testpass123"
    }

    response = requests.post(url, data=data)  # Note: data, not json for OAuth2
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")

    if response.status_code == 200:
        return result.get("access_token")
    return None


def test_get_current_user(token):
    """Test getting current user with token"""
    print("\n=== Testing Get Current User ===")
    url = f"{BASE_URL}/api/v1/auth/me"
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(url, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    return response.status_code == 200


def main():
    """Run all tests"""
    print("Starting Authentication Tests...")
    print(f"Server: {BASE_URL}")

    # Test health check first
    print("\n=== Testing Health Check ===")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

    if response.status_code != 200:
        print("\n❌ Server is not running! Start it with: uvicorn app.main:app --reload")
        return

    # Run auth tests
    test_register()
    token = test_login()

    if token:
        test_get_current_user(token)
        print("\n✅ All tests completed!")
    else:
        print("\n❌ Login failed, cannot test protected endpoint")


if __name__ == "__main__":
    main()
