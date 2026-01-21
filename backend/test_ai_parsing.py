#!/usr/bin/env python
"""
Test script for AI plan parsing endpoints
Run this after starting the server with: uvicorn app.main:app --reload

NOTE: This requires either ANTHROPIC_API_KEY or OPENAI_API_KEY in your .env file
"""

import requests
import json
import io

BASE_URL = "http://localhost:8000"


def create_sample_pdf():
    """Create a simple test PDF file in memory"""
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
/Length 300
>>
stream
BT
/F1 12 Tf
50 700 Td
(CONSTRUCTION BID SCHEDULE) Tj
0 -30 Td
(Item 101: Clearing and Grubbing - 1.0 LS) Tj
0 -20 Td
(Item 102: Excavation - 500 CY) Tj
0 -20 Td
(Item 103: Concrete Pavement - 1000 SY) Tj
0 -30 Td
(Specifications: ASTM C150, AASHTO M180) Tj
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
670
%%EOF"""
    return io.BytesIO(pdf_content)


def get_auth_token():
    """Register and login to get auth token"""
    print("\n=== Getting Auth Token ===")

    # Try to register (may fail if user exists)
    register_url = f"{BASE_URL}/api/v1/auth/register"
    register_data = {
        "email": "ai_test@example.com",
        "password": "testpass123",
        "name": "AI Test User",
        "company_name": "AI Test Co"
    }

    requests.post(register_url, json=register_data)

    # Login
    login_url = f"{BASE_URL}/api/v1/auth/login"
    login_data = {
        "username": "ai_test@example.com",
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
        "name": "AI Parsing Test Project",
        "job_number": f"AI-TEST-001",
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


def upload_test_plan(token, project_id):
    """Upload a test plan"""
    print("\n=== Uploading Test Plan ===")
    url = f"{BASE_URL}/api/v1/projects/{project_id}/documents"
    headers = {"Authorization": f"Bearer {token}"}

    pdf_file = create_sample_pdf()

    files = {
        "file": ("test_bid_schedule.pdf", pdf_file, "application/pdf")
    }
    data = {
        "doc_type": "plan"
    }

    response = requests.post(url, headers=headers, files=files, data=data)
    if response.status_code in [200, 201]:
        document_id = response.json()["id"]
        print(f"✅ Uploaded plan: {document_id}")
        return document_id
    else:
        print(f"❌ Upload failed: {response.json()}")
        return None


def test_ai_status(token):
    """Test AI service status"""
    print("\n=== Test: AI Service Status ===")
    url = f"{BASE_URL}/api/v1/ai/status"
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(url, headers=headers)
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")

    if result["claude_available"]:
        print("✅ Claude API is available")
    else:
        print("⚠️  Claude API not available - add ANTHROPIC_API_KEY to .env")

    if result["openai_available"]:
        print("✅ OpenAI API is available")
    else:
        print("ℹ️  OpenAI API not available")

    return response.status_code == 200


def test_parse_plan(token, project_id, document_id):
    """Test parsing a plan document"""
    print("\n=== Test: Parse Plan Document ===")
    url = f"{BASE_URL}/api/v1/ai/projects/{project_id}/documents/{document_id}/parse?max_pages=1"
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.post(url, headers=headers)
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")

    if response.status_code == 200 and result.get("success"):
        print(f"✅ Successfully parsed plan using {result.get('method')}")

        # Show parsed data
        if result.get("data"):
            data = result["data"]
            print(f"\n📊 Parsed Data:")

            if "bid_items" in data:
                print(f"  Bid Items: {len(data['bid_items'])}")
                for item in data["bid_items"][:3]:  # Show first 3
                    print(f"    - {item.get('item_number')}: {item.get('description')} ({item.get('quantity')} {item.get('unit')})")

            if "specifications" in data:
                print(f"  Specifications: {len(data['specifications'])}")
                for spec in data["specifications"][:3]:
                    print(f"    - {spec.get('code')}: {spec.get('description')}")

            if "project_info" in data:
                print(f"  Project Info: {data['project_info']}")

        return True
    else:
        print(f"❌ Parsing failed: {result.get('error', 'Unknown error')}")
        return False


def test_parse_and_save(token, project_id, document_id):
    """Test parsing and saving to database"""
    print("\n=== Test: Parse and Save to Database ===")
    url = f"{BASE_URL}/api/v1/ai/projects/{project_id}/documents/{document_id}/parse-and-save?max_pages=1"
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.post(url, headers=headers)
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")

    if response.status_code == 200 and result.get("success"):
        print(f"✅ Successfully saved {result.get('items_saved', 0)} items to database")
        return True
    else:
        print(f"❌ Save failed: {result.get('error', 'Unknown error')}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("AI PLAN PARSING TESTS")
    print("=" * 60)
    print(f"Server: {BASE_URL}")
    print("\nNOTE: This requires AI API keys in your .env file")
    print("      Add ANTHROPIC_API_KEY for Claude 3.5 Sonnet")
    print("=" * 60)

    # Get auth token
    token = get_auth_token()
    if not token:
        print("\n❌ Cannot proceed without auth token")
        return

    # Check AI status first
    test_ai_status(token)

    # Create project
    project_id = create_test_project(token)
    if not project_id:
        print("\n❌ Cannot proceed without project")
        return

    # Upload test plan
    document_id = upload_test_plan(token, project_id)
    if not document_id:
        print("\n❌ Cannot proceed without uploaded document")
        return

    # Run parsing tests
    tests = [
        ("Parse Plan Document", lambda: test_parse_plan(token, project_id, document_id)),
        ("Parse and Save to DB", lambda: test_parse_and_save(token, project_id, document_id)),
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
        print("\nNote: If Claude API is not available, parsing will fall back to OCR")


if __name__ == "__main__":
    main()
