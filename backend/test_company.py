#!/usr/bin/env python
"""
Test script for company settings endpoints
Run this after starting the server with: uvicorn app.main:app --reload
"""

import requests
import json

BASE_URL = "http://localhost:8000"


def get_auth_token():
    """Register and login to get auth token"""
    print("\n=== Getting Auth Token ===")

    # Try to register (may fail if user exists)
    register_url = f"{BASE_URL}/api/v1/auth/register"
    register_data = {
        "email": "company_test@example.com",
        "password": "testpass123",
        "name": "Company Test User",
        "company_name": "Test Construction Co"
    }

    requests.post(register_url, json=register_data)

    # Login
    login_url = f"{BASE_URL}/api/v1/auth/login"
    login_data = {
        "username": "company_test@example.com",
        "password": "testpass123"
    }

    response = requests.post(login_url, data=login_data)
    if response.status_code == 200:
        token = response.json()["access_token"]
        print(f"✅ Got auth token")
        return token
    else:
        print(f"❌ Login failed: {response.json()}")
        return None


def test_get_company(token):
    """Test getting company info"""
    print("\n=== Test: Get Company Info ===")
    url = f"{BASE_URL}/api/v1/company/me"
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(url, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    return response.status_code == 200


def test_update_company(token):
    """Test updating company info"""
    print("\n=== Test: Update Company Info ===")
    url = f"{BASE_URL}/api/v1/company/me"
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "name": "Updated Construction Company"
    }

    response = requests.put(url, headers=headers, json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    return response.status_code == 200


def test_get_rate_examples(token):
    """Test getting rate examples"""
    print("\n=== Test: Get Rate Examples ===")
    url = f"{BASE_URL}/api/v1/company/rates/examples"
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(url, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    return response.status_code == 200


def test_create_company_rates(token):
    """Test creating company rates"""
    print("\n=== Test: Create Company Rates ===")
    url = f"{BASE_URL}/api/v1/company/rates"
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "labor_rate_json": {
            "foreman": 45.00,
            "operator": 35.00,
            "laborer": 25.00,
            "equipment_operator": 38.00
        },
        "equipment_rate_json": {
            "excavator": 125.00,
            "bulldozer": 150.00,
            "dump_truck": 85.00,
            "concrete_mixer": 95.00,
            "crane": 200.00
        },
        "overhead_json": {
            "percentage": 15.0,
            "fixed_costs": 10000.00,
            "insurance": 5000.00,
            "office": 3000.00
        },
        "margin_json": {
            "default_percentage": 10.0,
            "minimum_percentage": 5.0,
            "target_percentage": 12.0
        }
    }

    response = requests.post(url, headers=headers, json=data)
    print(f"Status: {response.status_code}")

    if response.status_code in [200, 201]:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return True
    else:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        # If rates already exist, that's ok for this test
        if "already exist" in response.json().get("detail", ""):
            print("ℹ️  Rates already exist, skipping creation")
            return True
        return False


def test_get_company_rates(token):
    """Test getting company rates"""
    print("\n=== Test: Get Company Rates ===")
    url = f"{BASE_URL}/api/v1/company/rates"
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(url, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    return response.status_code == 200


def test_update_company_rates(token):
    """Test updating company rates"""
    print("\n=== Test: Update Company Rates ===")
    url = f"{BASE_URL}/api/v1/company/rates"
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "labor_rate_json": {
            "foreman": 50.00,  # Updated rate
            "operator": 40.00,  # Updated rate
            "laborer": 28.00,   # Updated rate
            "equipment_operator": 42.00  # Updated rate
        }
    }

    response = requests.put(url, headers=headers, json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    return response.status_code == 200


def main():
    """Run all tests"""
    print("=" * 60)
    print("COMPANY SETTINGS ENDPOINT TESTS")
    print("=" * 60)
    print(f"Server: {BASE_URL}")

    # Get auth token
    token = get_auth_token()
    if not token:
        print("\n❌ Cannot proceed without auth token")
        return

    # Run tests
    tests = [
        ("Get Company Info", lambda: test_get_company(token)),
        ("Update Company Info", lambda: test_update_company(token)),
        ("Get Rate Examples", lambda: test_get_rate_examples(token)),
        ("Create Company Rates", lambda: test_create_company_rates(token)),
        ("Get Company Rates", lambda: test_get_company_rates(token)),
        ("Update Company Rates", lambda: test_update_company_rates(token)),
        ("Get Updated Rates", lambda: test_get_company_rates(token)),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ Test failed with exception: {str(e)}")
            results.append((test_name, False))

    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")


if __name__ == "__main__":
    main()
