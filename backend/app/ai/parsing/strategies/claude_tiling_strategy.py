"""
Claude Tiling Strategy

Implements a two-phase map-reduce approach:
1. Coarse Pass: Low-res scan to identify regions of interest (ROI)
2. Detail Pass: High-res tiling of important regions only

This fixes the 5MB image limit bug by ensuring no tile exceeds the size limit.
"""

import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from fuzzywuzzy import fuzz

from anthropic import Anthropic

from ..base_strategy import BaseParsingStrategy, ParseResult, DocumentMetrics, StrategyType
from ..utils.image_processor import ImageProcessor, TileInfo
from ..utils.coordinate_mapper import CoordinateMapper, BoundingBox

logger = logging.getLogger(__name__)


class ClaudeTilingStrategy(BaseParsingStrategy):
    """
    Claude vision with intelligent tiling to handle large documents

    Strategy:
    - Phase 1 (Coarse): Low-res scan to identify ROI with bounding boxes
    - Phase 2 (Detail): High-res tiling only on important regions
    - Phase 3 (Aggregate): Map-reduce merge with deduplication
    """

    def _get_strategy_type(self) -> StrategyType:
        return StrategyType.CLAUDE_TILING

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)

        # Initialize Claude client
        api_key = config.get("anthropic_api_key")
        if api_key:
            self.client = Anthropic(api_key=api_key)
        else:
            self.client = None

        # Image processor
        max_size_mb = config.get("max_image_size_mb", 4.5)
        self.image_processor = ImageProcessor(max_size_mb=max_size_mb)

        # Coordinate mapper
        self.coord_mapper = CoordinateMapper()

        # Configuration
        self.coarse_dpi = config.get("coarse_scan_dpi", 100)
        self.detail_dpi = config.get("detail_scan_dpi", 200)
        self.tile_overlap = config.get("tile_overlap_percent", 0.1)
        self.max_concurrent = config.get("max_concurrent_tiles", 5)
        self.fuzzy_threshold = config.get("fuzzy_match_threshold", 85)
        self.model = config.get("claude_model", "claude-sonnet-4-5-20250929")
        self.max_tokens = config.get("claude_max_tokens", 16000)
        self.temperature = config.get("claude_temperature", 0.0)

    def is_available(self) -> bool:
        """Check if Claude API is configured"""
        enabled = self.config.get("enable_claude_parsing", True)
        return enabled and self.client is not None

    def can_handle(self, metrics: DocumentMetrics) -> bool:
        """Claude tiling can handle any document size"""
        return True

    def get_priority(self) -> int:
        """Priority 3 - universal fallback"""
        return 3

    async def parse(self, pdf_path: Path, max_pages: int = 5) -> ParseResult:
        """
        Parse PDF using two-phase tiling approach

        Args:
            pdf_path: Path to PDF file
            max_pages: Maximum pages to process

        Returns:
            ParseResult with extracted data
        """
        start_time = time.time()
        logger.info(f"Starting Claude tiling strategy for {pdf_path}")

        try:
            # Phase 1: Coarse scan for ROI detection
            logger.info("Phase 1: Coarse scan for ROI detection")
            roi_list = await self._coarse_scan(pdf_path, max_pages)

            if not roi_list:
                # No ROI detected, parse entire pages at low resolution
                logger.warning("No ROI detected, parsing entire pages")
                result_data = await self._parse_full_pages(pdf_path, max_pages)
            else:
                # Phase 2: Detail pass on ROI
                logger.info(f"Phase 2: Detail pass on {len(roi_list)} ROI regions")
                result_data = await self._detail_pass(pdf_path, roi_list)

            # Calculate metrics
            processing_time = int((time.time() - start_time) * 1000)

            # Calculate confidence based on data completeness
            confidence = self._calculate_confidence(result_data)

            return ParseResult(
                success=True,
                data=result_data,
                strategy_used=StrategyType.CLAUDE_TILING,
                confidence_score=confidence,
                pages_processed=max_pages,
                processing_time_ms=processing_time,
                metadata={
                    "roi_regions": len(roi_list),
                    "method": "tiling",
                },
            )

        except Exception as e:
            logger.error(f"Claude tiling strategy failed: {e}", exc_info=True)
            processing_time = int((time.time() - start_time) * 1000)

            return ParseResult(
                success=False,
                error=str(e),
                strategy_used=StrategyType.CLAUDE_TILING,
                processing_time_ms=processing_time,
            )

    async def _coarse_scan(
        self,
        pdf_path: Path,
        max_pages: int
    ) -> List[BoundingBox]:
        """
        Phase 1: Scan pages at low resolution to identify regions of interest

        Args:
            pdf_path: Path to PDF
            max_pages: Maximum pages to scan

        Returns:
            List of bounding boxes for important regions
        """
        roi_prompt = """
Analyze this construction plan page and identify regions of interest (ROI) that contain important information.

Look for:
- Bid item tables (with item numbers, descriptions, quantities)
- Specification sections
- Project information (name, location, dates)
- Material lists or schedules

For each region, provide a bounding box in this format:
{
  "regions": [
    {
      "label": "bid_items_table",
      "x": 100,
      "y": 200,
      "width": 800,
      "height": 600,
      "confidence": 0.9
    }
  ]
}

Return ONLY the JSON. If no important regions found, return {"regions": []}.
"""

        all_roi = []

        for page_num in range(1, min(max_pages + 1, 6)):
            try:
                # Convert page at low resolution
                image, base64_data = self.image_processor.pdf_page_to_image(
                    pdf_path,
                    page_num,
                    dpi=self.coarse_dpi,
                    target_size_mb=2.0  # Lower size for coarse scan
                )

                # Ask Claude to identify ROI
                content = [
                    {"type": "text", "text": roi_prompt},
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": base64_data
                        }
                    }
                ]

                message = self.client.messages.create(
                    model=self.model,
                    max_tokens=2048,
                    temperature=self.temperature,
                    messages=[{"role": "user", "content": content}]
                )

                response_text = message.content[0].text

                # Parse ROI response
                roi_data = self._parse_json_response(response_text)

                if roi_data and "regions" in roi_data:
                    for region in roi_data["regions"]:
                        bbox = BoundingBox(
                            x=region.get("x", 0),
                            y=region.get("y", 0),
                            width=region.get("width", image.width),
                            height=region.get("height", image.height),
                            page_number=page_num,
                            confidence=region.get("confidence", 0.8),
                            label=region.get("label", "unknown"),
                        )
                        all_roi.append(bbox)

                logger.info(f"Page {page_num}: Found {len(roi_data.get('regions', []))} ROI regions")

            except Exception as e:
                logger.warning(f"Failed to scan page {page_num}: {e}")
                continue

        logger.info(f"Coarse scan complete: {len(all_roi)} total ROI regions")
        return all_roi

    async def _detail_pass(
        self,
        pdf_path: Path,
        roi_list: List[BoundingBox]
    ) -> Dict[str, Any]:
        """
        Phase 2: Process ROI at high resolution with tiling

        Args:
            pdf_path: Path to PDF
            roi_list: List of ROI bounding boxes

        Returns:
            Aggregated parsed data
        """
        all_results = []

        # Group ROI by page
        by_page = {}
        for roi in roi_list:
            if roi.page_number not in by_page:
                by_page[roi.page_number] = []
            by_page[roi.page_number].append(roi)

        # Process each page's ROI
        for page_num, page_rois in by_page.items():
            logger.info(f"Processing page {page_num} with {len(page_rois)} ROI regions")

            try:
                # Convert page at high resolution
                image, _ = self.image_processor.pdf_page_to_image(
                    pdf_path,
                    page_num,
                    dpi=self.detail_dpi,
                )

                # Process each ROI
                for roi in page_rois:
                    # Create tiles for this ROI
                    tile_size = self.image_processor.calculate_tile_size(
                        roi.width,
                        roi.height,
                        self.image_processor.max_size_bytes,
                        dpi=self.detail_dpi
                    )

                    tiles = self.image_processor.create_tiles(
                        image,
                        page_num,
                        tile_size,
                        overlap_percent=self.tile_overlap,
                        roi=roi
                    )

                    logger.info(f"Created {len(tiles)} tiles for ROI '{roi.label}'")

                    # Process tiles with concurrency limit
                    tile_results = await self._process_tiles_concurrent(tiles)
                    all_results.extend(tile_results)

            except Exception as e:
                logger.error(f"Failed to process page {page_num}: {e}")
                continue

        # Phase 3: Aggregate results
        logger.info("Phase 3: Aggregating and deduplicating results")
        final_data = self._aggregate_results(all_results)

        return final_data

    async def _process_tiles_concurrent(
        self,
        tiles: List[TileInfo]
    ) -> List[Dict[str, Any]]:
        """
        Process multiple tiles concurrently with rate limiting

        Args:
            tiles: List of tiles to process

        Returns:
            List of parsed results from each tile
        """
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def process_with_semaphore(tile: TileInfo) -> Optional[Dict[str, Any]]:
            async with semaphore:
                return await self._process_tile_with_claude(tile)

        tasks = [process_with_semaphore(tile) for tile in tiles]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out failed results
        valid_results = []
        for result in results:
            if isinstance(result, dict):
                valid_results.append(result)
            elif isinstance(result, Exception):
                logger.warning(f"Tile processing failed: {result}")

        return valid_results

    async def _process_tile_with_claude(
        self,
        tile: TileInfo
    ) -> Optional[Dict[str, Any]]:
        """
        Process a single tile with Claude

        Args:
            tile: Tile to process

        Returns:
            Parsed data from tile
        """
        extraction_prompt = """
Analyze this section of a construction plan. Extract ANY of the following you can see:

**Materials/Items**: Lumber (2x4, 2x6, etc.), hardware, roofing, windows, doors, concrete, drywall, insulation, etc.
**Quantities**: Counts, dimensions, areas (e.g., "100 SF", "24 EA", "12 LF")
**Specifications**: Codes, standards, material grades, brands
**Project Info**: Name, location, lot number, builder

Return JSON in this EXACT format:
{
  "bid_items": [{"item_number": "1", "description": "2x4 studs", "quantity": 100, "unit": "EA"}],
  "materials": [{"name": "2x4 Pine Studs", "quantity": 100, "unit": "EA"}],
  "specifications": [{"code": "#2 Pine", "description": "Framing lumber grade"}],
  "project_info": {"name": "Lot 195", "location": "Lafayette", "bid_date": null}
}

IMPORTANT:
- Extract materials/lumber from drawings, notes, schedules
- Look for dimensions like "2x4", "2x6", quantities like "@ 16\" O.C."
- Include window/door schedules
- Return ONLY JSON, no other text
- If nothing found, return empty arrays but valid JSON
"""

        try:
            content = [
                {"type": "text", "text": extraction_prompt},
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": tile.base64_data
                    }
                }
            ]

            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[{"role": "user", "content": content}]
            )

            response_text = message.content[0].text

            # Parse response
            data = self._parse_json_response(response_text)

            # DEBUG: Log what we got from Claude
            if data:
                bid_count = len(data.get("bid_items", []))
                mat_count = len(data.get("materials", []))
                spec_count = len(data.get("specifications", []))

                if bid_count > 0 or mat_count > 0 or spec_count > 0:
                    logger.info(f"Tile {tile.tile_number}: Found {bid_count} bids, {mat_count} mats, {spec_count} specs")
                else:
                    logger.debug(f"Tile {tile.tile_number}: No items extracted (empty response)")

                # Add tile metadata
                data["_tile_meta"] = {
                    "page": tile.page_number,
                    "tile": tile.tile_number,
                    "x": tile.x,
                    "y": tile.y,
                }
            else:
                logger.warning(f"Tile {tile.tile_number}: Failed to parse JSON response")
                logger.debug(f"Response text: {response_text[:500]}")

            return data

        except Exception as e:
            logger.error(f"Failed to process tile {tile.tile_number}: {e}")
            return None

    async def _parse_full_pages(
        self,
        pdf_path: Path,
        max_pages: int
    ) -> Dict[str, Any]:
        """
        Fallback: Parse entire pages at low resolution (when no ROI detected)

        Args:
            pdf_path: Path to PDF
            max_pages: Maximum pages

        Returns:
            Parsed data
        """
        extraction_prompt = """
You are analyzing a construction plan document. Extract the following information:

1. **Bid Items**: List all bid items with their item numbers, descriptions, quantities, and units.
2. **Specifications**: List any specification codes or references (e.g., ASTM, AASHTO).
3. **Project Details**: Extract project name, location, bid date if visible.
4. **Materials**: List specific materials mentioned with quantities.

Return the data in this JSON format:
{
  "bid_items": [
    {
      "item_number": "101",
      "description": "Clearing and Grubbing",
      "quantity": 1.0,
      "unit": "LS"
    }
  ],
  "specifications": [
    {
      "code": "ASTM C150",
      "description": "Portland Cement"
    }
  ],
  "project_info": {
    "name": null,
    "location": null,
    "bid_date": null
  },
  "materials": [
    {
      "name": "Concrete",
      "quantity": 500,
      "unit": "CY"
    }
  ]
}

Be thorough but only include items explicitly mentioned. Use null or empty arrays if not found.
"""

        try:
            content = [{"type": "text", "text": extraction_prompt}]

            # Add pages as images
            for page_num in range(1, min(max_pages + 1, 6)):
                try:
                    _, base64_data = self.image_processor.pdf_page_to_image(
                        pdf_path,
                        page_num,
                        dpi=self.coarse_dpi,
                        target_size_mb=3.0
                    )

                    content.append({
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": base64_data
                        }
                    })

                except Exception as e:
                    logger.warning(f"Failed to add page {page_num}: {e}")

            # Call Claude
            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[{"role": "user", "content": content}]
            )

            response_text = message.content[0].text
            data = self._parse_json_response(response_text)

            return data or {}

        except Exception as e:
            logger.error(f"Failed to parse full pages: {e}")
            return {}

    def _aggregate_results(
        self,
        results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Aggregate and deduplicate results from multiple tiles

        Args:
            results: List of parsed results

        Returns:
            Merged and deduplicated data
        """
        aggregated = {
            "bid_items": [],
            "specifications": [],
            "project_info": {},
            "materials": [],
        }

        # Collect all items
        all_bid_items = []
        all_specs = []
        all_materials = []
        project_infos = []

        for result in results:
            if not result:
                continue

            all_bid_items.extend(result.get("bid_items", []))
            all_specs.extend(result.get("specifications", []))
            all_materials.extend(result.get("materials", []))

            proj_info = result.get("project_info", {})
            if proj_info and any(v for v in proj_info.values() if v):
                project_infos.append(proj_info)

        # Deduplicate bid items
        aggregated["bid_items"] = self._deduplicate_items(
            all_bid_items,
            key_fields=["item_number", "description"]
        )

        # Deduplicate specifications
        aggregated["specifications"] = self._deduplicate_items(
            all_specs,
            key_fields=["code"]
        )

        # Deduplicate materials
        aggregated["materials"] = self._deduplicate_items(
            all_materials,
            key_fields=["name"]
        )

        # Merge project info (take most complete)
        aggregated["project_info"] = self._merge_project_info(project_infos)

        logger.info(
            f"Aggregation complete: "
            f"{len(aggregated['bid_items'])} bid items, "
            f"{len(aggregated['specifications'])} specs, "
            f"{len(aggregated['materials'])} materials"
        )

        return aggregated

    def _deduplicate_items(
        self,
        items: List[Dict[str, Any]],
        key_fields: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Deduplicate items using fuzzy matching

        Args:
            items: List of items
            key_fields: Fields to use for matching

        Returns:
            Deduplicated list
        """
        if not items:
            return []

        unique_items = []
        used_indices = set()

        for i, item in enumerate(items):
            if i in used_indices:
                continue

            # Build key for comparison
            key_values = []
            for field in key_fields:
                value = item.get(field, "")
                if value:
                    key_values.append(str(value).lower().strip())

            if not key_values:
                continue

            # Find duplicates
            matches = [i]
            for j, other in enumerate(items[i + 1:], start=i + 1):
                if j in used_indices:
                    continue

                # Build other key
                other_values = []
                for field in key_fields:
                    value = other.get(field, "")
                    if value:
                        other_values.append(str(value).lower().strip())

                if not other_values:
                    continue

                # Fuzzy match
                similarity = fuzz.ratio(" ".join(key_values), " ".join(other_values))

                if similarity >= self.fuzzy_threshold:
                    matches.append(j)
                    used_indices.add(j)

            # Merge matched items (take most complete)
            merged_item = self._merge_items([items[idx] for idx in matches])
            unique_items.append(merged_item)

        return unique_items

    def _merge_items(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge multiple similar items, preferring non-null values"""
        merged = {}

        for item in items:
            for key, value in item.items():
                if key.startswith("_"):
                    continue

                if key not in merged or merged[key] is None or merged[key] == "":
                    merged[key] = value

        return merged

    def _merge_project_info(
        self,
        project_infos: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Merge project info, preferring most complete"""
        if not project_infos:
            return {"name": None, "location": None, "bid_date": None}

        # Sort by completeness (number of non-null fields)
        sorted_infos = sorted(
            project_infos,
            key=lambda p: sum(1 for v in p.values() if v),
            reverse=True
        )

        # Start with most complete
        merged = dict(sorted_infos[0])

        # Fill in missing fields from others
        for info in sorted_infos[1:]:
            for key, value in info.items():
                if key not in merged or not merged[key]:
                    merged[key] = value

        return merged

    def _parse_json_response(self, text: str) -> Optional[Dict[str, Any]]:
        """Parse JSON from Claude response, handling markdown code blocks"""
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try extracting from markdown
            if "```json" in text:
                json_start = text.find("```json") + 7
                json_end = text.find("```", json_start)
                if json_end > json_start:
                    json_str = text[json_start:json_end].strip()
                    try:
                        return json.loads(json_str)
                    except json.JSONDecodeError:
                        pass

            logger.warning("Could not parse JSON from response")
            return None

    def _calculate_confidence(self, data: Dict[str, Any]) -> float:
        """Calculate confidence score based on data completeness"""
        score = 0.0

        # Bid items (most important)
        bid_items = data.get("bid_items", [])
        if bid_items:
            score += 0.4
            # Bonus for well-structured items
            complete_items = sum(
                1 for item in bid_items
                if item.get("item_number") and item.get("description")
            )
            score += 0.2 * min(complete_items / max(len(bid_items), 1), 1.0)

        # Project info
        proj_info = data.get("project_info", {})
        if proj_info and any(v for v in proj_info.values() if v):
            score += 0.2

        # Specifications
        if data.get("specifications"):
            score += 0.1

        # Materials
        if data.get("materials"):
            score += 0.1

        return min(score, 1.0)
