"""
Test Claude API connection and diagnose issues
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

def test_api_key():
    """Check if API key is set"""
    key = os.getenv("ANTHROPIC_API_KEY", "")

    print("="*60)
    print("CLAUDE API CONNECTION DIAGNOSTICS")
    print("="*60)

    print("\n1. API Key Check:")
    if not key:
        print("   ERROR: ANTHROPIC_API_KEY not found in .env file")
        return False
    elif len(key) < 20:
        print(f"   ERROR: API key too short ({len(key)} chars) - likely invalid")
        return False
    elif not key.startswith("sk-ant-"):
        print(f"   ERROR: API key doesn't start with 'sk-ant-'")
        return False
    else:
        print(f"   OK: API key found ({len(key)} chars)")
        print(f"   Prefix: {key[:15]}...")
        return True

def test_anthropic_import():
    """Test if anthropic package is installed"""
    print("\n2. Anthropic Package:")
    try:
        import anthropic
        print(f"   OK: anthropic package installed (v{anthropic.__version__})")
        return True
    except ImportError as e:
        print(f"   ERROR: anthropic package not installed: {e}")
        return False

def test_api_connection():
    """Test actual API connection"""
    print("\n3. API Connection Test:")
    try:
        from app.ai.config import anthropic_client

        if not anthropic_client:
            print("   ERROR: anthropic_client is None (API key not configured)")
            return False

        print("   Attempting to connect to Claude API...")

        # Try a simple API call
        message = anthropic_client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=10,
            messages=[{
                "role": "user",
                "content": "Say 'OK'"
            }]
        )

        response = message.content[0].text
        print(f"   OK: API connection successful!")
        print(f"   Response: {response}")
        return True

    except Exception as e:
        print(f"   ERROR: API connection failed")
        print(f"   Error type: {type(e).__name__}")
        print(f"   Error message: {str(e)}")

        # Specific error guidance
        if "Connection" in str(e) or "connection" in str(e):
            print("\n   DIAGNOSIS: Network connection issue")
            print("   Possible causes:")
            print("   - No internet connection")
            print("   - Firewall blocking API requests")
            print("   - Proxy configuration needed")
            print("   - VPN interfering with connection")
        elif "authentication" in str(e).lower() or "api key" in str(e).lower():
            print("\n   DIAGNOSIS: API key issue")
            print("   Possible causes:")
            print("   - Invalid API key")
            print("   - Expired API key")
            print("   - API key not activated")
        elif "rate" in str(e).lower():
            print("\n   DIAGNOSIS: Rate limit exceeded")
        else:
            print("\n   DIAGNOSIS: Unknown error - see message above")

        return False

def main():
    step1 = test_api_key()
    if not step1:
        print("\nFIX: Add valid ANTHROPIC_API_KEY to backend/.env file")
        print("Get your key from: https://console.anthropic.com/settings/keys")
        return

    step2 = test_anthropic_import()
    if not step2:
        print("\nFIX: pip install anthropic")
        return

    step3 = test_api_connection()

    print("\n" + "="*60)
    if step3:
        print("SUCCESS: Claude API is working!")
        print("You can now use the parsing functionality.")
    else:
        print("FAILED: Cannot connect to Claude API")
        print("Fix the issues above before trying to parse documents.")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
