import logging
import os
from pathlib import Path
from typing import Dict, List, Optional
import json

from app.ai.config import anthropic_client, openai_client, is_ai_available
from app.ai.ocr_service import ocr_service
from app.ai.parsing.config import load_parsing_config, get_strategy_config
from app.ai.parsing.strategy_selector import StrategySelector

logger = logging.getLogger(__name__)


class PlanParser:
    """
    Parse construction plans and extract bid items, quantities, and specifications
    Uses multi-strategy intelligent routing with automatic fallback
    """

    def __init__(self):
        self.anthropic = anthropic_client
        self.openai = openai_client

        # Initialize new multi-strategy system
        try:
            parsing_config = load_parsing_config()
            config_dict = get_strategy_config(parsing_config)
            self.strategy_selector = StrategySelector(config_dict)
            logger.info("Multi-strategy parsing system initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize multi-strategy system: {e}")
            self.strategy_selector = None

    async def parse_plan_with_claude(
        self,
        pdf_path: Path,
        max_pages: int = 5
    ) -> Dict:
        """
        Parse construction plan using Claude Vision API (legacy method)

        Note: Uses whatever model is set in CLAUDE_MODEL env var
        Default: claude-sonnet-4-5-20250929

        Args:
            pdf_path: Path to PDF plan
            max_pages: Maximum pages to analyze

        Returns:
            Dictionary with extracted data
        """
        logger.info("=" * 60)
        logger.info("[CLAUDE PARSE] Starting document parsing")
        logger.info(f"[CLAUDE PARSE] PDF Path: {pdf_path}")
        logger.info(f"[CLAUDE PARSE] Max Pages: {max_pages}")
        logger.info("=" * 60)
        
        if not self.anthropic:
            logger.error("[CLAUDE PARSE] ERROR: Claude API not configured - check ANTHROPIC_API_KEY")
            return {
                "success": False,
                "error": "Claude API not configured"
            }

        try:
            # Convert first few pages to base64 images
            logger.info("[CLAUDE PARSE] Step 1: Converting PDF pages to images...")
            images = []
            total_size_mb = 0
            for page_num in range(1, min(max_pages + 1, 6)):
                logger.info(f"[CLAUDE PARSE]   Converting page {page_num}...")
                img_base64 = ocr_service.pdf_page_to_base64(pdf_path, page_num)
                if img_base64:
                    images.append(img_base64)
                    img_size_mb = len(img_base64) * 3 / 4 / 1024 / 1024
                    total_size_mb += img_size_mb
                    logger.info(f"[CLAUDE PARSE]   Page {page_num}: {img_size_mb:.2f}MB - SUCCESS")
                else:
                    logger.warning(f"[CLAUDE PARSE]   Page {page_num}: FAILED to convert")

            if not images:
                logger.error("[CLAUDE PARSE] ERROR: No images could be converted from PDF")
                return {
                    "success": False,
                    "error": "Failed to convert PDF pages to images"
                }

            logger.info(f"[CLAUDE PARSE] Step 1 Complete: {len(images)} pages, total payload: {total_size_mb:.2f}MB")

            # Create prompt for Claude - optimized for lumber yard material takeoffs
            # Uses EXACT Stine catalog naming conventions for accurate matching
            prompt = """
You are a lumber yard estimator analyzing construction plan documents for STINE Home + Yard.
Extract a COMPLETE material takeoff using STINE's EXACT product naming format.

CRITICAL NAMING FORMAT - Use these EXACT patterns:
LUMBER (use "Pine #2" prefix):
- "Pine #2 (2x4-8 Nominal)" for 2x4 8-foot boards
- "Pine #2 (2x4-10 Nominal)" for 2x4 10-foot boards  
- "Pine #2 (2x4-12 Nominal)" for 2x4 12-foot boards
- "Pine #2 (2x4-14 Nominal)" for 2x4 14-foot boards
- "Pine #2 (2x4-16 Nominal)" for 2x4 16-foot boards
- "Pine #2 (2x6-8 Nominal)" through "Pine #2 (2x6-20 Nominal)"
- "Pine #2 (2x8-10 Nominal)" through "Pine #2 (2x8-16 Nominal)"
- "Pine #2 (2x10-12 Nominal)" through "Pine #2 (2x10-16 Nominal)"
- "Pine #2 (2x12-14 Nominal)" for headers/beams

STUDS (use "Stud-" prefix):
- "Stud- Spruce Pine Fir (2x4-116-5/8 Nominal)" for 9-foot studs
- "Stud- Spruce, Pine, Fir (2x4-140-5/8 Nominal)" for 11-foot studs
- "Stud Spruce (2x6-116-5/8 Nominal)" for 2x6 studs

TREATED LUMBER:
- "Pine #2 PRIME TREATED (2x4-14 Nominal)" for treated plates
- "Pine #2 PRIME TREATED (2x6-14 Nominal)" for treated sills

SHEATHING:
- "OSB 7/16\" Rated Sheathing (48x96x7/16)" for wall sheathing
- "OSB 7/16\" Radiant Barrier (48x96x7/16)" for roof sheathing
- "OSB 10' Wind (48x121-1/8x7/16)" for 10-foot panels

ROOFING:
- "Roof Tamko Hert Wthrwd" for shingles (unit: BDL)
- "Stine ProFelt Plus Synthetic Felt" for underlayment (unit: RL)
- "Drip Edge 26ga" for drip edge
- "Vent Ridge Shngle Over" for ridge vent

SIDING:
- "Hardie Lap Siding 6 1/4 Smooth" for lap siding
- "Hardie Trim 4/4x3.5x12 Smooth" for trim
- "Hardie Soffit Vented 16x12 Smooth" for vented soffit
- "Hardie Soffit Non-Vented 16x12 Smooth" for solid soffit

HARDWARE:
- "Simpson 18 Ga. Galvanized Steel Hurricane Tie H2.5A" for hurricane ties
- "Simpson ZMax LUS26Z Joist Hanger" for joist hangers
- "Anchor Bolt HDG 5/8 10\"" for anchor bolts

INSULATION:
- "Insul R-13 125.94 SqFt 3-1/2x15" for R-13
- "Insul R-30 58.67 Sq' 9.25x16" for R-30

DRYWALL:
- "Gypsum 4'x12'x1/2\" Reg" for regular drywall
- "Gypsum 4'X8'X1/2\" Mold/Moist Resistant Purple" for moisture resistant

Return ONLY valid JSON:
{
  "project_info": {"name": "", "lot_number": "", "builder": ""},
  "materials": [
    {"name": "Pine #2 (2x4-14 Nominal)", "quantity": 80, "unit": "ea", "category": "Walls"},
    {"name": "Stud- Spruce Pine Fir (2x4-116-5/8 Nominal)", "quantity": 220, "unit": "ea", "category": "Walls"},
    {"name": "OSB 7/16\" Radiant Barrier (48x96x7/16)", "quantity": 100, "unit": "ea", "category": "Sheathing"},
    {"name": "Simpson 18 Ga. Galvanized Steel Hurricane Tie H2.5A", "quantity": 160, "unit": "ea", "category": "Hardware"}
  ],
  "bid_items": [],
  "specifications": []
}

Extract ALL materials with quantities. A typical house has 50-150 line items.
"""

            # Build content with multiple images
            content = [
                {
                    "type": "text",
                    "text": prompt
                }
            ]

            for img_base64 in images:
                content.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",  # FIXED: was PNG, now JPEG
                        "data": img_base64
                    }
                })

            # Call Claude API - use model from env var or default
            claude_model = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5-20250929")
            logger.info(f"[CLAUDE PARSE] Step 2: Calling Claude API")
            logger.info(f"[CLAUDE PARSE]   Model: {claude_model}")
            logger.info(f"[CLAUDE PARSE]   Images: {len(images)}")
            logger.info(f"[CLAUDE PARSE]   Prompt length: {len(prompt)} chars")

            # Add retry logic for connection errors
            max_retries = 3
            retry_count = 0
            last_error = None

            while retry_count < max_retries:
                try:
                    logger.info(f"[CLAUDE PARSE]   Sending request (attempt {retry_count + 1}/{max_retries})...")
                    message = self.anthropic.messages.create(
                        model=claude_model,
                        max_tokens=4096,
                        messages=[{
                            "role": "user",
                            "content": content
                        }],
                        timeout=120.0  # 2 minute timeout
                    )
                    logger.info(f"[CLAUDE PARSE]   API call successful!")
                    break  # Success, exit retry loop

                except Exception as api_error:
                    last_error = api_error
                    retry_count += 1
                    error_msg = str(api_error)
                    logger.error(f"[CLAUDE PARSE]   API Error: {error_msg}")

                    if "Connection" in error_msg or "connection" in error_msg:
                        if retry_count < max_retries:
                            logger.warning(f"[CLAUDE PARSE]   Connection error, retrying in 2 seconds...")
                            import time
                            time.sleep(2)
                        else:
                            logger.error(f"[CLAUDE PARSE] FAILED: Connection failed after {max_retries} attempts")
                            raise Exception(f"Failed to connect to Claude API after {max_retries} attempts. Check your internet connection.")
                    else:
                        # Non-connection error, don't retry
                        raise

            # Extract response text
            response_text = message.content[0].text
            logger.info(f"[CLAUDE PARSE] Step 3: Processing response")
            logger.info(f"[CLAUDE PARSE]   Response length: {len(response_text)} chars")
            logger.info(f"[CLAUDE PARSE]   Response preview: {response_text[:500]}...")

            # Try to parse JSON
            try:
                parsed_data = json.loads(response_text)
                logger.info(f"[CLAUDE PARSE]   JSON parsed directly")
            except json.JSONDecodeError:
                logger.info(f"[CLAUDE PARSE]   Direct JSON parse failed, looking for code blocks...")
                # If not valid JSON, try to extract JSON from markdown code blocks
                if "```json" in response_text:
                    json_start = response_text.find("```json") + 7
                    json_end = response_text.find("```", json_start)
                    json_str = response_text[json_start:json_end].strip()
                    parsed_data = json.loads(json_str)
                    logger.info(f"[CLAUDE PARSE]   JSON extracted from code block")
                else:
                    logger.error(f"[CLAUDE PARSE] ERROR: Could not parse JSON from response")
                    logger.error(f"[CLAUDE PARSE] Full response: {response_text}")
                    raise ValueError("Could not parse JSON from response")

            # Log extraction results
            bid_items = parsed_data.get("bid_items", [])
            materials = parsed_data.get("materials", [])
            specs = parsed_data.get("specifications", [])
            project_info = parsed_data.get("project_info", {})
            
            logger.info("=" * 60)
            logger.info("[CLAUDE PARSE] EXTRACTION RESULTS:")
            logger.info(f"[CLAUDE PARSE]   Bid Items: {len(bid_items)}")
            for i, item in enumerate(bid_items[:5]):
                logger.info(f"[CLAUDE PARSE]     {i+1}. {item.get('description', 'N/A')[:50]} - Qty: {item.get('quantity', 'N/A')} {item.get('unit', '')}")
            if len(bid_items) > 5:
                logger.info(f"[CLAUDE PARSE]     ... and {len(bid_items) - 5} more")
                
            logger.info(f"[CLAUDE PARSE]   Materials: {len(materials)}")
            for i, mat in enumerate(materials[:5]):
                logger.info(f"[CLAUDE PARSE]     {i+1}. {mat.get('name', 'N/A')[:50]} - Qty: {mat.get('quantity', 'N/A')} {mat.get('unit', '')}")
            if len(materials) > 5:
                logger.info(f"[CLAUDE PARSE]     ... and {len(materials) - 5} more")
                
            logger.info(f"[CLAUDE PARSE]   Specifications: {len(specs)}")
            logger.info(f"[CLAUDE PARSE]   Project Info: {project_info}")
            logger.info("=" * 60)

            return {
                "success": True,
                "data": parsed_data,
                "pages_analyzed": len(images)
            }

        except Exception as e:
            error_type = type(e).__name__
            error_msg = str(e)
            logger.error("=" * 60)
            logger.error(f"[CLAUDE PARSE] EXCEPTION OCCURRED")
            logger.error(f"[CLAUDE PARSE]   Type: {error_type}")
            logger.error(f"[CLAUDE PARSE]   Message: {error_msg}")
            logger.error("=" * 60)

            # Provide user-friendly error messages
            if "Connection" in error_msg or "connection" in error_msg:
                user_error = "Network connection error. Please check your internet connection and try again."
            elif "authentication" in error_msg.lower() or "api key" in error_msg.lower():
                user_error = "API authentication failed. Please check your ANTHROPIC_API_KEY in .env file."
            elif "timeout" in error_msg.lower():
                user_error = "Request timed out. The document may be too large. Try reducing max_pages."
            elif "rate" in error_msg.lower():
                user_error = "API rate limit exceeded. Please wait a moment and try again."
            else:
                user_error = f"Claude API error: {error_msg}"

            return {
                "success": False,
                "error": user_error,
                "technical_error": f"{error_type}: {error_msg}"
            }

    async def parse_plan_with_ocr(
        self,
        pdf_path: Path,
        max_pages: int = 5
    ) -> Dict:
        """
        Fallback: Extract text using OCR and basic parsing

        Args:
            pdf_path: Path to PDF plan
            max_pages: Maximum pages to process

        Returns:
            Dictionary with extracted text
        """
        try:
            page_texts = ocr_service.extract_text_from_pdf(pdf_path, max_pages)

            if not page_texts:
                return {
                    "success": False,
                    "error": "OCR failed to extract text"
                }

            return {
                "success": True,
                "data": {
                    "raw_text": page_texts,
                    "pages_analyzed": len(page_texts)
                },
                "method": "ocr"
            }

        except Exception as e:
            logger.error(f"Failed to parse plan with OCR: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def parse_plan(
        self,
        pdf_path: Path,
        max_pages: int = 5,
        use_ai: bool = True
    ) -> Dict:
        """
        Parse construction plan using best available method

        Args:
            pdf_path: Path to PDF plan
            max_pages: Maximum pages to analyze
            use_ai: Whether to use AI (Claude) if available

        Returns:
            Dictionary with parsed data
        """
        # TEMPORARILY DISABLED: Multi-strategy tiling has extraction issues
        # Using proven legacy Claude method that works reliably

        ai_status = is_ai_available()

        # Try Claude first if available and requested
        if use_ai and ai_status["claude"]:
            logger.info("Parsing plan with Claude Vision (proven method)")
            result = await self.parse_plan_with_claude(pdf_path, max_pages)
            if result["success"]:
                return result

        # Fallback to OCR
        logger.info("Falling back to OCR parsing")
        return await self.parse_plan_with_ocr(pdf_path, max_pages)


# Singleton instance
plan_parser = PlanParser()
