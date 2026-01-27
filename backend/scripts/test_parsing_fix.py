"""
Test the fixed parsing with Lot 195 plan
"""

import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.ai.plan_parser import plan_parser
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_parsing():
    """Test parsing with the fixed tile creation"""
    logger.info("="*60)
    logger.info("Testing Fixed Claude Tiling Strategy")
    logger.info("="*60)

    plan_path = Path("uploads/stine/Lot 195 pdfs.pdf")

    if not plan_path.exists():
        logger.error(f"Plan not found at: {plan_path}")
        return

    logger.info(f"Parsing: {plan_path}")
    logger.info(f"File size: {plan_path.stat().st_size / 1024 / 1024:.2f} MB\n")

    # Parse with AI
    result = await plan_parser.parse_plan(
        pdf_path=plan_path,
        max_pages=5,
        use_ai=True
    )

    print("\n" + "="*60)
    print("PARSING RESULTS")
    print("="*60)

    if not result["success"]:
        print(f"❌ FAILED: {result.get('error')}")
        return

    print(f"✅ SUCCESS!")
    print(f"Strategy: {result.get('strategy', 'unknown')}")
    print(f"Pages: {result.get('pages_analyzed')}")
    print(f"Time: {result.get('processing_time_ms', 0)/1000:.1f}s")
    print(f"Confidence: {result.get('confidence', 0):.2f}")

    data = result.get("data", {})

    # Count items
    bid_items = data.get("bid_items", [])
    materials = data.get("materials", [])
    specs = data.get("specifications", [])

    print(f"\n📊 Extracted Data:")
    print(f"  - Bid items: {len(bid_items)}")
    print(f"  - Materials: {len(materials)}")
    print(f"  - Specifications: {len(specs)}")

    if bid_items:
        print(f"\n📋 Sample Bid Items (first 5):")
        for item in bid_items[:5]:
            desc = item.get("description", "N/A")
            qty = item.get("quantity", 0)
            unit = item.get("unit", "")
            print(f"  • {desc}: {qty} {unit}")

    if materials:
        print(f"\n🔨 Sample Materials (first 5):")
        for mat in materials[:5]:
            name = mat.get("name", "N/A")
            qty = mat.get("quantity", 0)
            unit = mat.get("unit", "")
            print(f"  • {name}: {qty} {unit}")

    print("\n" + "="*60)

    if len(bid_items) == 0 and len(materials) == 0:
        print("⚠️  WARNING: No items extracted!")
        print("Check if tiles were created and processed properly.")
    else:
        print("✅ Tiles created and items extracted successfully!")

    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(test_parsing())
