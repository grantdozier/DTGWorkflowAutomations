"""
Image Processor

Utilities for image optimization, tiling, and compression for document parsing.
"""

import base64
import io
import logging
import math
from pathlib import Path
from typing import List, Tuple, Optional
from dataclasses import dataclass

from pdf2image import convert_from_path
from PIL import Image
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class TileInfo:
    """Information about a tile"""
    image: Image.Image
    base64_data: str
    x: int
    y: int
    width: int
    height: int
    page_number: int
    tile_number: int
    total_tiles: int


class ImageProcessor:
    """Processes images for document parsing"""

    def __init__(self, max_size_mb: float = 4.5):
        """
        Initialize image processor

        Args:
            max_size_mb: Maximum size in MB for images (default 4.5MB for safety margin)
        """
        self.max_size_bytes = int(max_size_mb * 1024 * 1024)

    def pdf_page_to_image(
        self,
        pdf_path: Path,
        page_number: int,
        dpi: int = 200,
        target_size_mb: Optional[float] = None
    ) -> Tuple[Image.Image, str]:
        """
        Convert a PDF page to an optimized image with size limit

        Args:
            pdf_path: Path to PDF file
            page_number: Page number (1-indexed)
            dpi: Target DPI for rendering
            target_size_mb: Target size in MB (default uses max_size_mb)

        Returns:
            Tuple of (PIL Image, base64 encoded string)
        """
        target_bytes = int(target_size_mb * 1024 * 1024) if target_size_mb else self.max_size_bytes

        logger.debug(f"Converting page {page_number} at {dpi} DPI")

        # Convert PDF page to image
        images = convert_from_path(
            str(pdf_path),
            first_page=page_number,
            last_page=page_number,
            dpi=dpi,
        )

        if not images:
            raise ValueError(f"Could not convert page {page_number}")

        image = images[0]

        # Optimize image size
        optimized_image, base64_data = self.optimize_image_size(image, target_bytes)

        actual_size = len(base64_data) * 3 / 4  # Base64 overhead
        logger.debug(
            f"Page {page_number}: "
            f"size={actual_size/1024/1024:.2f}MB, "
            f"dimensions={optimized_image.size}"
        )

        return optimized_image, base64_data

    def optimize_image_size(
        self,
        image: Image.Image,
        target_bytes: int,
        format: str = "JPEG"
    ) -> Tuple[Image.Image, str]:
        """
        Optimize image size through iterative compression

        Args:
            image: PIL Image to optimize
            target_bytes: Target size in bytes
            format: Output format (JPEG or PNG)

        Returns:
            Tuple of (optimized Image, base64 string)
        """
        # Convert to RGB if needed (for JPEG)
        if format == "JPEG" and image.mode in ("RGBA", "P", "LA"):
            # Create white background
            rgb_image = Image.new("RGB", image.size, (255, 255, 255))
            if image.mode == "P":
                image = image.convert("RGBA")
            rgb_image.paste(image, mask=image.split()[-1] if image.mode in ("RGBA", "LA") else None)
            image = rgb_image

        # HIGH-QUALITY compression to preserve microscopic detail in construction plans
        # Since tiles are already small, minimal compression should be needed
        quality = 95
        min_quality = 90  # CHANGED: Keep quality very high for detail preservation

        while quality >= min_quality:
            buffer = io.BytesIO()
            image.save(buffer, format=format, quality=quality, optimize=True)
            size = buffer.tell()

            if size <= target_bytes:
                # Success - encode to base64
                buffer.seek(0)
                base64_data = base64.b64encode(buffer.read()).decode('utf-8')
                logger.debug(f"Optimized to {size/1024/1024:.2f}MB at quality={quality}")
                return image, base64_data

            # Reduce quality minimally
            quality -= 1  # CHANGED: Very small steps to maintain quality

        # If still too large even at quality 90, the tile is too big
        # Solution: Create smaller tiles, DON'T resize (which loses detail)
        logger.error(
            f"Tile size {image.size} exceeds target even at quality {min_quality}. "
            f"Size: {size/1024/1024:.2f}MB, Target: {target_bytes/1024/1024:.2f}MB. "
            f"This suggests tiles should be smaller. Returning at quality 90."
        )

        # Return at quality 90 anyway - better to exceed limit slightly than lose detail
        # Claude will handle slightly larger images in practice
        buffer = io.BytesIO()
        image.save(buffer, format=format, quality=90, optimize=True)
        buffer.seek(0)
        base64_data = base64.b64encode(buffer.read()).decode('utf-8')

        actual_mb = len(base64_data) * 3 / 4 / 1024 / 1024
        logger.warning(f"Returning tile at {actual_mb:.2f}MB (quality 90) - may exceed target")

        return image, base64_data

    def create_tiles(
        self,
        image: Image.Image,
        page_number: int,
        tile_size: Tuple[int, int],
        overlap_percent: float = 0.1,
        roi: Optional['BoundingBox'] = None
    ) -> List[TileInfo]:
        """
        Split an image into overlapping tiles

        Args:
            image: PIL Image to tile
            page_number: Page number for reference
            tile_size: (width, height) of each tile
            overlap_percent: Percentage of overlap between tiles (0.0-0.5)
            roi: Optional region of interest to tile (defaults to full image)

        Returns:
            List of TileInfo objects
        """
        tile_width, tile_height = tile_size

        # Determine region to tile
        if roi:
            x_start, y_start = roi.x, roi.y
            region_width, region_height = roi.width, roi.height
            # Crop to ROI
            region_image = image.crop((x_start, y_start, x_start + region_width, y_start + region_height))
        else:
            x_start, y_start = 0, 0
            region_width, region_height = image.size
            region_image = image

        # Calculate step size with overlap
        step_x = int(tile_width * (1 - overlap_percent))
        step_y = int(tile_height * (1 - overlap_percent))

        tiles = []
        tile_number = 0

        # SPECIAL CASE: If the ROI is smaller than the tile size, use it as a single tile
        if region_width <= tile_width and region_height <= tile_height:
            logger.debug(f"ROI ({region_width}x{region_height}) fits in single tile")

            # Optimize and encode the entire ROI
            _, base64_data = self.optimize_image_size(region_image, self.max_size_bytes)

            tile_info = TileInfo(
                image=region_image,
                base64_data=base64_data,
                x=x_start,
                y=y_start,
                width=region_width,
                height=region_height,
                page_number=page_number,
                tile_number=0,
                total_tiles=1,
            )

            tiles.append(tile_info)
            logger.info(f"Created 1 tile (full ROI) for page {page_number}")
            return tiles

        # NORMAL CASE: ROI is larger than tile size, split into tiles
        # Generate tiles
        for y in range(0, region_height, step_y):
            for x in range(0, region_width, step_x):
                # Calculate tile bounds
                x_end = min(x + tile_width, region_width)
                y_end = min(y + tile_height, region_height)

                # Skip tiles that are too small (less than 25% of target size)
                # This prevents tiny edge fragments
                min_tile_size = max(tile_width // 4, tile_height // 4)
                if (x_end - x) < min_tile_size or (y_end - y) < min_tile_size:
                    logger.debug(f"Skipping tiny tile fragment at ({x},{y})")
                    continue

                # Crop tile
                tile_image = region_image.crop((x, y, x_end, y_end))

                # Optimize and encode
                _, base64_data = self.optimize_image_size(tile_image, self.max_size_bytes)

                # Create TileInfo
                tile_info = TileInfo(
                    image=tile_image,
                    base64_data=base64_data,
                    x=x_start + x,
                    y=y_start + y,
                    width=x_end - x,
                    height=y_end - y,
                    page_number=page_number,
                    tile_number=tile_number,
                    total_tiles=0,  # Will update after all tiles created
                )

                tiles.append(tile_info)
                tile_number += 1

        # Update total tiles count
        for tile in tiles:
            tile.total_tiles = len(tiles)

        logger.info(f"Created {len(tiles)} tiles for page {page_number}")

        return tiles

    def calculate_tile_size(
        self,
        image_width: int,
        image_height: int,
        target_size_bytes: int,
        dpi: int = 200
    ) -> Tuple[int, int]:
        """
        Calculate optimal tile size to stay under target size

        UPDATED: Conservative calculation for high-quality JPEG (90-95)

        Args:
            image_width: Width of source image
            image_height: Height of source image
            target_size_bytes: Target size per tile in bytes
            dpi: DPI of image

        Returns:
            (tile_width, tile_height) in pixels
        """
        # HIGH QUALITY JPEG (90-95) has less compression
        # At quality 90-95, compression ratio is ~1:3 to 1:5, not 1:10
        # Use CONSERVATIVE estimate to ensure tiles stay under limit
        bytes_per_pixel = 0.7  # CHANGED from 0.3 to 0.7 for high quality

        # Add 20% safety margin to target
        safe_target = target_size_bytes * 0.8

        # Calculate max pixels per tile
        max_pixels = safe_target / bytes_per_pixel

        # Calculate aspect ratio
        aspect_ratio = image_width / image_height

        # Calculate tile dimensions maintaining aspect ratio
        tile_height = int(math.sqrt(max_pixels / aspect_ratio))
        tile_width = int(tile_height * aspect_ratio)

        # Cap maximum tile dimensions (prevent massive tiles)
        max_tile_dimension = 2000  # ADDED: Hard cap at 2000 pixels per side
        if tile_width > max_tile_dimension or tile_height > max_tile_dimension:
            if tile_width > tile_height:
                scale = max_tile_dimension / tile_width
            else:
                scale = max_tile_dimension / tile_height
            tile_width = int(tile_width * scale)
            tile_height = int(tile_height * scale)

        # Ensure reasonable minimum size
        min_dimension = 500
        if tile_width < min_dimension or tile_height < min_dimension:
            scale = max(min_dimension / tile_width, min_dimension / tile_height)
            tile_width = int(tile_width * scale)
            tile_height = int(tile_height * scale)

        estimated_mb = tile_width * tile_height * bytes_per_pixel / 1024 / 1024
        logger.debug(
            f"Calculated tile size: {tile_width}x{tile_height} "
            f"(estimated {estimated_mb:.2f}MB, target {target_size_bytes/1024/1024:.2f}MB)"
        )

        return tile_width, tile_height

    def image_to_base64(
        self,
        image: Image.Image,
        format: str = "JPEG",
        quality: int = 85
    ) -> str:
        """
        Convert PIL Image to base64 string

        Args:
            image: PIL Image
            format: Output format (JPEG or PNG)
            quality: JPEG quality (1-100)

        Returns:
            Base64 encoded string
        """
        buffer = io.BytesIO()

        # Convert to RGB for JPEG if needed
        if format == "JPEG" and image.mode in ("RGBA", "P", "LA"):
            rgb_image = Image.new("RGB", image.size, (255, 255, 255))
            if image.mode == "P":
                image = image.convert("RGBA")
            rgb_image.paste(image, mask=image.split()[-1] if image.mode in ("RGBA", "LA") else None)
            image = rgb_image

        image.save(buffer, format=format, quality=quality, optimize=True)
        buffer.seek(0)

        return base64.b64encode(buffer.read()).decode('utf-8')
