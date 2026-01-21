#!/usr/bin/env python
"""
Test script for estimation engine endpoints
Run this after starting the server with: uvicorn app.main:app --reload

This tests the complete estimation workflow:
1. Create project
2. Upload and parse plan document
3. Generate cost estimate
4. View estimate details
"""

import requests
import json
import io

BASE_URL = "http://localhost:8000"


def create_sample_pdf():
    """Create a simple test PDF with bid items"""
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
/Length 400
>>
stream
BT
/F1 14 Tf
50 720 Td
(CONSTRUCTION BID SCHEDULE) Tj
0 -40 Td
/F1 12 Tf
(Item 101: Clearing and Grubbing - 1.0 LS) Tj
0 -20 Td
(Item 102: Excavation - 500 CY) Tj
0 -20 Td
(Item 103: Concrete Pavement - 1000 SY) Tj
0 -20 Td
(Item 104: Curb and Gutter - 2000 LF) Tj
0 -20 Td
(Item 105: Traffic Signage - 25 EA) Tj
0 -40 Td
(Specifications: ASTM C150, AASHTO M180) Tj
0 -20 Td
(Project: Highway 90 Expansion, Lafayette LA) Tj
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
771
%%EOF"""
    return io.BytesIO(pdf_content)


def get_auth_token():
    """Register and login to get auth token"""
    print("\n=== Getting Auth Token ===")

    # Try to register (may fail if user exists)
    register_url = f"{BASE_URL}/api/v1/auth/register"
    register_data = {
        "email": "estimation_test@example.com",
        "password": "testpass123",
        "name": "Estimation Test User",
        "company_name": "Estimation Test Co"
    }

    requests.post(register_url, json=register_data)

    # Login
    login_url = f"{BASE_URL}/api/v1/auth/login"
    login_data = {
        "username": "estimation_test@example.com",
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


def setup_company_rates(token):
    """Set up company rates for estimation"""
    print("\n=== Setting Up Company Rates ===")
    url = f"{BASE_URL}/api/v1/company/rates"
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "labor_rate_json": {
            "foreman": 50.00,
            "operator": 40.00,
            "laborer": 30.00
        },
        "equipment_rate_json": {
            "excavator": 125.00,
            "bulldozer": 150.00
        },
        "overhead_json": {
            "percentage": 15.0,
            "fixed_costs": 10000.00
        },
        "margin_json": {
            "default_percentage": 10.0,
            "minimum_percentage": 5.0
        }
    }

    response = requests.post(url, headers=headers, json=data)
    if response.status_code in [200, 201, 400]:  # 400 if already exists
        print(f"✅ Company rates configured")
        return True
    else:
        print(f"⚠️  Failed to configure rates: {response.json()}")
        return True  # Continue anyway


def create_test_project(token):
    """Create a test project"""
    print("\n=== Creating Test Project ===")
    url = f"{BASE_URL}/api/v1/projects"
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "name": "Estimation Test Project",
        "job_number": f"EST-TEST-001",
        "location": "Lafayette, LA",
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


def upload_and_parse_plan(token, project_id):
    """Upload a plan and parse it"""
    print("\n=== Uploading and Parsing Plan ===")

    # Upload plan
    upload_url = f"{BASE_URL}/api/v1/projects/{project_id}/documents"
    headers = {"Authorization": f"Bearer {token}"}
    pdf_file = create_sample_pdf()

    files = {"file": ("estimation_test_plan.pdf", pdf_file, "application/pdf")}
    data = {"doc_type": "plan"}

    upload_response = requests.post(upload_url, headers=headers, files=files, data=data)
    if upload_response.status_code not in [200, 201]:
        print(f"❌ Upload failed: {upload_response.json()}")
        return None

    document_id = upload_response.json()["id"]
    print(f"✅ Uploaded plan: {document_id}")

    # Parse and save the plan
    parse_url = f"{BASE_URL}/api/v1/ai/projects/{project_id}/documents/{document_id}/parse-and-save?max_pages=1"
    parse_response = requests.post(parse_url, headers=headers)

    if parse_response.status_code == 200:
        result = parse_response.json()
        print(f"✅ Parsed plan: {result.get('items_saved', 0)} items extracted")
        return document_id
    else:
        print(f"⚠️  Parse failed, but continuing: {parse_response.json()}")
        # Continue anyway - might not have AI configured
        return document_id


def test_generate_estimate(token, project_id):
    """Test generating an estimate"""
    print("\n=== Test: Generate Estimate ===")
    url = f"{BASE_URL}/api/v1/projects/{project_id}/estimate"
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "include_takeoffs": True,
        "include_bid_items": True
    }

    response = requests.post(url, headers=headers, json=data)
    print(f"Status: {response.status_code}")

    if response.status_code in [200, 201]:
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")

        print(f"\n💰 Estimate Summary:")
        breakdown = result.get("breakdown", {})
        print(f"  Materials: ${breakdown.get('materials', 0):,.2f}")
        print(f"  Labor: ${breakdown.get('labor', 0):,.2f}")
        print(f"  Equipment: ${breakdown.get('equipment', 0):,.2f}")
        print(f"  Subtotal: ${breakdown.get('subtotal', 0):,.2f}")
        print(f"  Overhead: ${breakdown.get('overhead', 0):,.2f}")
        print(f"  Profit: ${breakdown.get('profit', 0):,.2f}")
        print(f"  TOTAL: ${breakdown.get('total', 0):,.2f}")

        return result["estimate"]["id"]
    else:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return None


def test_list_estimates(token, project_id):
    """Test listing estimates"""
    print("\n=== Test: List Estimates ===")
    url = f"{BASE_URL}/api/v1/projects/{project_id}/estimates"
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(url, headers=headers)
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")

    return response.status_code == 200


def test_get_estimate_detail(token, project_id, estimate_id):
    """Test getting estimate details"""
    print("\n=== Test: Get Estimate Detail ===")
    url = f"{BASE_URL}/api/v1/projects/{project_id}/estimates/{estimate_id}"
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(url, headers=headers)
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")

    return response.status_code == 200


def test_generate_with_custom_margins(token, project_id):
    """Test generating estimate with custom overhead and profit"""
    print("\n=== Test: Generate Estimate with Custom Margins ===")
    url = f"{BASE_URL}/api/v1/projects/{project_id}/estimate"
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "include_takeoffs": True,
        "overhead_percentage": 20.0,
        "profit_percentage": 15.0
    }

    response = requests.post(url, headers=headers, json=data)
    print(f"Status: {response.status_code}")

    if response.status_code in [200, 201]:
        result = response.json()
        print(f"\n💰 Custom Margins Estimate:")
        breakdown = result.get("breakdown", {})
        print(f"  Overhead (20%): ${breakdown.get('overhead', 0):,.2f}")
        print(f"  Profit (15%): ${breakdown.get('profit', 0):,.2f}")
        print(f"  TOTAL: ${breakdown.get('total', 0):,.2f}")
        return True
    else:
        print(f"Failed: {response.json()}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("ESTIMATION ENGINE TESTS")
    print("=" * 60)
    print(f"Server: {BASE_URL}")

    # Get auth token
    token = get_auth_token()
    if not token:
        print("\n❌ Cannot proceed without auth token")
        return

    # Setup company rates
    setup_company_rates(token)

    # Create project
    project_id = create_test_project(token)
    if not project_id:
        print("\n❌ Cannot proceed without project")
        return

    # Upload and parse plan
    document_id = upload_and_parse_plan(token, project_id)

    # Generate estimate
    estimate_id = test_generate_estimate(token, project_id)

    if not estimate_id:
        print("\n❌ Failed to generate estimate")
        return

    # Run additional tests
    tests = [
        ("List Estimates", lambda: test_list_estimates(token, project_id)),
        ("Get Estimate Detail", lambda: test_get_estimate_detail(token, project_id, estimate_id)),
        ("Generate with Custom Margins", lambda: test_generate_with_custom_margins(token, project_id)),
        ("List All Estimates Again", lambda: test_list_estimates(token, project_id)),
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
        print("\n✨ The complete estimation system is working!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")


if __name__ == "__main__":
    main()
