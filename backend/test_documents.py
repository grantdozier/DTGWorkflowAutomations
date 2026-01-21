#!/usr/bin/env python
"""
Test script for document upload endpoints
Run this after starting the server with: uvicorn app.main:app --reload
"""

import requests
import json
import io
from pathlib import Path

BASE_URL = "http://localhost:8000"


def create_sample_pdf():
    """Create a simple test PDF file in memory"""
    # Create a minimal valid PDF
    pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/Resources <<
/Font <<
/F1 <<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
>>
>>
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj
4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(Test PDF Document) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000317 00000 n
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
409
%%EOF"""
    return io.BytesIO(pdf_content)


def get_auth_token():
    """Register and login to get auth token"""
    print("\n=== Getting Auth Token ===")

    # Try to register (may fail if user exists)
    register_url = f"{BASE_URL}/api/v1/auth/register"
    register_data = {
        "email": "document_test@example.com",
        "password": "testpass123",
        "name": "Document Test User",
        "company_name": "Test Documents Co"
    }

    requests.post(register_url, json=register_data)

    # Login
    login_url = f"{BASE_URL}/api/v1/auth/login"
    login_data = {
        "username": "document_test@example.com",
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


def create_test_project(token):
    """Create a test project"""
    print("\n=== Creating Test Project ===")
    url = f"{BASE_URL}/api/v1/projects"
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "name": "Document Upload Test Project",
        "job_number": f"DOC-TEST-001",
        "location": "Test Location",
        "type": "state"
    }

    response = requests.post(url, headers=headers, json=data)
    if response.status_code in [200, 201]:
        project_id = response.json()["id"]
        print(f"✅ Created project: {project_id}")
        return project_id
    else:
        # Try to get existing project
        response = requests.get(f"{BASE_URL}/api/v1/projects", headers=headers)
        if response.status_code == 200:
            projects = response.json()["projects"]
            if projects:
                project_id = projects[0]["id"]
                print(f"✅ Using existing project: {project_id}")
                return project_id
        print(f"❌ Failed to create/get project")
        return None


def test_upload_plan(token, project_id):
    """Test uploading a plan document"""
    print("\n=== Test: Upload Plan ===")
    url = f"{BASE_URL}/api/v1/projects/{project_id}/documents"
    headers = {"Authorization": f"Bearer {token}"}

    # Create test PDF
    pdf_file = create_sample_pdf()

    files = {
        "file": ("test_plan.pdf", pdf_file, "application/pdf")
    }
    data = {
        "doc_type": "plan"
    }

    response = requests.post(url, headers=headers, files=files, data=data)
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")

    if response.status_code in [200, 201]:
        return result.get("id")
    return None


def test_upload_spec(token, project_id):
    """Test uploading a spec document"""
    print("\n=== Test: Upload Specification ===")
    url = f"{BASE_URL}/api/v1/projects/{project_id}/documents"
    headers = {"Authorization": f"Bearer {token}"}

    # Create test PDF
    pdf_file = create_sample_pdf()

    files = {
        "file": ("test_spec.pdf", pdf_file, "application/pdf")
    }
    data = {
        "doc_type": "spec"
    }

    response = requests.post(url, headers=headers, files=files, data=data)
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")

    if response.status_code in [200, 201]:
        return result.get("id")
    return None


def test_list_documents(token, project_id):
    """Test listing all documents"""
    print("\n=== Test: List All Documents ===")
    url = f"{BASE_URL}/api/v1/projects/{project_id}/documents"
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(url, headers=headers)
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")

    return response.status_code == 200


def test_list_documents_by_type(token, project_id, doc_type):
    """Test listing documents filtered by type"""
    print(f"\n=== Test: List Documents (Type: {doc_type}) ===")
    url = f"{BASE_URL}/api/v1/projects/{project_id}/documents?doc_type={doc_type}"
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(url, headers=headers)
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")

    return response.status_code == 200


def test_download_document(token, project_id, document_id):
    """Test downloading a document"""
    print("\n=== Test: Download Document ===")
    url = f"{BASE_URL}/api/v1/projects/{project_id}/documents/{document_id}"
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(url, headers=headers)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        print(f"✅ Downloaded file, size: {len(response.content)} bytes")
        print(f"Content-Type: {response.headers.get('content-type')}")
        return True
    else:
        print(f"❌ Download failed: {response.text}")
        return False


def test_upload_invalid_file(token, project_id):
    """Test uploading an invalid file type"""
    print("\n=== Test: Upload Invalid File Type ===")
    url = f"{BASE_URL}/api/v1/projects/{project_id}/documents"
    headers = {"Authorization": f"Bearer {token}"}

    # Create a text file (not PDF)
    txt_file = io.BytesIO(b"This is not a PDF")

    files = {
        "file": ("test.txt", txt_file, "text/plain")
    }
    data = {
        "doc_type": "plan"
    }

    response = requests.post(url, headers=headers, files=files, data=data)
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")

    # Should fail with 400
    if response.status_code == 400:
        print("✅ Correctly rejected invalid file type")
        return True
    else:
        print("❌ Should have rejected invalid file type")
        return False


def test_delete_document(token, project_id, document_id):
    """Test deleting a document"""
    print("\n=== Test: Delete Document ===")
    url = f"{BASE_URL}/api/v1/projects/{project_id}/documents/{document_id}"
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.delete(url, headers=headers)
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")

    return response.status_code == 200


def main():
    """Run all tests"""
    print("=" * 60)
    print("DOCUMENT UPLOAD ENDPOINT TESTS")
    print("=" * 60)
    print(f"Server: {BASE_URL}")

    # Get auth token
    token = get_auth_token()
    if not token:
        print("\n❌ Cannot proceed without auth token")
        return

    # Create test project
    project_id = create_test_project(token)
    if not project_id:
        print("\n❌ Cannot proceed without project")
        return

    # Upload test documents
    plan_id = test_upload_plan(token, project_id)
    spec_id = test_upload_spec(token, project_id)

    if not plan_id or not spec_id:
        print("\n❌ Failed to upload documents, cannot continue tests")
        return

    # Run tests
    tests = [
        ("List All Documents", lambda: test_list_documents(token, project_id)),
        ("List Plans Only", lambda: test_list_documents_by_type(token, project_id, "plan")),
        ("List Specs Only", lambda: test_list_documents_by_type(token, project_id, "spec")),
        ("Download Plan", lambda: test_download_document(token, project_id, plan_id)),
        ("Download Spec", lambda: test_download_document(token, project_id, spec_id)),
        ("Upload Invalid File", lambda: test_upload_invalid_file(token, project_id)),
        ("Delete Document", lambda: test_delete_document(token, project_id, plan_id)),
        ("List After Delete", lambda: test_list_documents(token, project_id)),
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
