"""
FINAL TEST - Prove the system works end-to-end
"""

import asyncio
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from app.ai.plan_parser import plan_parser

async def test():
    print("\n" + "="*60)
    print("TESTING: Lot 195 Parsing with Claude Vision")
    print("="*60 + "\n")

    plan_path = Path("uploads/stine/Lot 195 pdfs.pdf")

    print(f"File: {plan_path}")
    print(f"Size: {plan_path.stat().st_size / 1024 / 1024:.2f} MB")
    print(f"\nParsing 5 pages with Claude Vision...")
    print("(This will take 30-60 seconds...)\n")

    result = await plan_parser.parse_plan_with_claude(
        plan_path,
        max_pages=5
    )

    print("="*60)

    if not result["success"]:
        print("FAILED:", result.get("error"))
        return

    print("SUCCESS!")
    print("="*60)

    data = result.get("data", {})
    bid_items = data.get("bid_items", [])
    materials = data.get("materials", [])
    specs = data.get("specifications", [])
    proj_info = data.get("project_info", {})

    print(f"\nExtracted:")
    print(f"  - Bid Items: {len(bid_items)}")
    print(f"  - Materials: {len(materials)}")
    print(f"  - Specifications: {len(specs)}")

    if proj_info:
        print(f"\nProject Info:")
        if proj_info.get("name"):
            print(f"  - Name: {proj_info['name']}")
        if proj_info.get("location"):
            print(f"  - Location: {proj_info['location']}")

    if bid_items:
        print(f"\nSample Bid Items:")
        for item in bid_items[:3]:
            desc = item.get("description", "N/A")
            qty = item.get("quantity", 0)
            unit = item.get("unit", "")
            print(f"  • {desc}: {qty} {unit}")

    if materials:
        print(f"\nSample Materials:")
        for mat in materials[:5]:
            name = mat.get("name", "N/A")
            qty = mat.get("quantity", 0)
            unit = mat.get("unit", "")
            print(f"  • {name}: {qty} {unit}")

    total_items = len(bid_items) + len(materials)

    print("\n" + "="*60)

    if total_items > 0:
        print(f"SUCCESS! Extracted {total_items} total items")
        print("The system is WORKING!")
    else:
        print("WARNING: Extracted 0 items")
        print("Claude may need a better prompt for this document type")

    print("="*60 + "\n")

if __name__ == "__main__":
    asyncio.run(test())
