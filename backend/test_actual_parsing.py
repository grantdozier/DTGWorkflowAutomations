"""
Test the actual parsing flow that runs when clicking "Parse with AI"
This simulates the exact API call the UI makes
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.ai.plan_parser import plan_parser

async def test_actual_parsing():
    """Test with the exact same code path as the API"""
    print("\n" + "="*70)
    print("TESTING ACTUAL PARSE FLOW (as called by API)")
    print("="*70 + "\n")

    plan_path = Path("uploads/stine/Lot 195 pdfs.pdf")

    if not plan_path.exists():
        print(f"ERROR: File not found: {plan_path}")
        return

    print(f"File: {plan_path}")
    print(f"Size: {plan_path.stat().st_size / 1024 / 1024:.2f} MB\n")

    print("Calling plan_parser.parse_plan()...")
    print("(This is what the API endpoint calls)")
    print("Please wait 30-60 seconds...\n")

    try:
        # This is EXACTLY what the API calls
        result = await plan_parser.parse_plan(
            pdf_path=plan_path,
            max_pages=5,
            use_ai=True
        )

        print("\n" + "="*70)
        print("RESULT:")
        print("="*70)

        print(f"\nSuccess: {result.get('success')}")

        if not result.get('success'):
            print(f"Error: {result.get('error')}")
            if result.get('technical_error'):
                print(f"Technical: {result.get('technical_error')}")
            print("\n" + "="*70)
            print("FAILED - See error above")
            print("="*70 + "\n")
            return

        data = result.get('data', {})
        bid_items = data.get('bid_items', [])
        materials = data.get('materials', [])

        print(f"Method: {result.get('method', 'unknown')}")
        print(f"Pages analyzed: {result.get('pages_analyzed', 0)}")
        print(f"\nExtracted:")
        print(f"  - Bid items: {len(bid_items)}")
        print(f"  - Materials: {len(materials)}")

        if materials:
            print(f"\nMaterials:")
            for mat in materials[:5]:
                print(f"  - {mat.get('name', 'Unknown')}: {mat.get('quantity', 0)} {mat.get('unit', '')}")

        total_items = len(bid_items) + len(materials)

        print("\n" + "="*70)
        if total_items > 0:
            print(f"SUCCESS! Extracted {total_items} items")
            print("This is exactly what the API would return")
        else:
            print("WARNING: 0 items extracted")
            print("Claude parsed successfully but found no itemized data")
        print("="*70 + "\n")

    except Exception as e:
        print(f"\nEXCEPTION: {type(e).__name__}")
        print(f"Message: {str(e)}")
        print("\n" + "="*70)
        print("FAILED - Exception occurred")
        print("="*70 + "\n")
        raise

if __name__ == "__main__":
    asyncio.run(test_actual_parsing())
