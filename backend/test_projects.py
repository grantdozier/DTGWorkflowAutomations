#!/usr/bin/env python
"""
Test script for project management endpoints
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
        "email": "project_test@example.com",
        "password": "testpass123",
        "name": "Project Test User",
        "company_name": "Test Projects Inc"
    }

    requests.post(register_url, json=register_data)

    # Login
    login_url = f"{BASE_URL}/api/v1/auth/login"
    login_data = {
        "username": "project_test@example.com",
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


def test_create_project(token):
    """Test creating a new project"""
    print("\n=== Test: Create Project ===")
    url = f"{BASE_URL}/api/v1/projects"
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "name": "Highway 90 Expansion",
        "job_number": "HWY-2024-001",
        "location": "Lafayette, LA",
        "type": "state"
    }

    response = requests.post(url, headers=headers, json=data)
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")

    if response.status_code in [200, 201]:
        return result.get("id")
    return None


def test_list_projects(token):
    """Test listing projects"""
    print("\n=== Test: List Projects ===")
    url = f"{BASE_URL}/api/v1/projects"
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(url, headers=headers)
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")

    return response.status_code == 200


def test_list_projects_with_filter(token):
    """Test listing projects with type filter"""
    print("\n=== Test: List Projects (Filter by Type) ===")
    url = f"{BASE_URL}/api/v1/projects?type=state"
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(url, headers=headers)
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")

    return response.status_code == 200


def test_get_project(token, project_id):
    """Test getting a specific project"""
    print("\n=== Test: Get Project ===")
    url = f"{BASE_URL}/api/v1/projects/{project_id}"
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(url, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    return response.status_code == 200


def test_update_project(token, project_id):
    """Test updating a project"""
    print("\n=== Test: Update Project ===")
    url = f"{BASE_URL}/api/v1/projects/{project_id}"
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "name": "Highway 90 Expansion - Updated",
        "location": "Lafayette and Youngsville, LA"
    }

    response = requests.put(url, headers=headers, json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    return response.status_code == 200


def test_list_project_documents(token, project_id):
    """Test listing project documents"""
    print("\n=== Test: List Project Documents ===")
    url = f"{BASE_URL}/api/v1/projects/{project_id}/documents"
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(url, headers=headers)
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")

    return response.status_code == 200


def test_list_project_bid_items(token, project_id):
    """Test listing project bid items"""
    print("\n=== Test: List Project Bid Items ===")
    url = f"{BASE_URL}/api/v1/projects/{project_id}/bid-items"
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(url, headers=headers)
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")

    return response.status_code == 200


def test_create_additional_projects(token):
    """Create a few more test projects"""
    print("\n=== Test: Create Additional Projects ===")
    headers = {"Authorization": f"Bearer {token}"}

    projects = [
        {
            "name": "Bridge Repair Project",
            "job_number": "BR-2024-002",
            "location": "Baton Rouge, LA",
            "type": "state"
        },
        {
            "name": "Commercial Building",
            "job_number": "CB-2024-003",
            "location": "New Orleans, LA",
            "type": "private"
        }
    ]

    for proj_data in projects:
        url = f"{BASE_URL}/api/v1/projects"
        response = requests.post(url, headers=headers, json=proj_data)
        status = "✅" if response.status_code in [200, 201] else "❌"
        print(f"{status} Created: {proj_data['name']} (Status: {response.status_code})")

    return True


def test_delete_project(token, project_id):
    """Test deleting a project"""
    print("\n=== Test: Delete Project ===")
    url = f"{BASE_URL}/api/v1/projects/{project_id}"
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.delete(url, headers=headers)
    print(f"Status: {response.status_code}")

    if response.status_code == 204:
        print("✅ Project deleted successfully")
        return True
    else:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("PROJECT MANAGEMENT ENDPOINT TESTS")
    print("=" * 60)
    print(f"Server: {BASE_URL}")

    # Get auth token
    token = get_auth_token()
    if not token:
        print("\n❌ Cannot proceed without auth token")
        return

    # Create a project
    project_id = test_create_project(token)

    if not project_id:
        print("\n❌ Failed to create project, cannot continue tests")
        return

    # Run tests
    tests = [
        ("List Projects", lambda: test_list_projects(token)),
        ("List Projects with Filter", lambda: test_list_projects_with_filter(token)),
        ("Get Project", lambda: test_get_project(token, project_id)),
        ("Update Project", lambda: test_update_project(token, project_id)),
        ("List Project Documents", lambda: test_list_project_documents(token, project_id)),
        ("List Project Bid Items", lambda: test_list_project_bid_items(token, project_id)),
        ("Create Additional Projects", lambda: test_create_additional_projects(token)),
        ("List All Projects Again", lambda: test_list_projects(token)),
        ("Delete Project", lambda: test_delete_project(token, project_id)),
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
