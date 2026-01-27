"""
Coordinate Mapper

Utilities for handling bounding boxes and coordinate transformations.
"""

import logging
from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict, Any

logger = logging.getLogger(__name__)


@dataclass
class BoundingBox:
    """Represents a bounding box with coordinates"""
    x: int
    y: int
    width: int
    height: int
    page_number: int = 1
    confidence: float = 1.0
    label: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "page_number": self.page_number,
            "confidence": self.confidence,
            "label": self.label,
        }

    def area(self) -> int:
        """Calculate area of bounding box"""
        return self.width * self.height

    def intersection_over_union(self, other: "BoundingBox") -> float:
        """
        Calculate IoU (Intersection over Union) with another bounding box

        Args:
            other: Another BoundingBox

        Returns:
            IoU score (0.0-1.0)
        """
        if self.page_number != other.page_number:
            return 0.0

        # Calculate intersection
        x1 = max(self.x, other.x)
        y1 = max(self.y, other.y)
        x2 = min(self.x + self.width, other.x + other.width)
        y2 = min(self.y + self.height, other.y + other.height)

        if x2 < x1 or y2 < y1:
            return 0.0

        intersection = (x2 - x1) * (y2 - y1)

        # Calculate union
        union = self.area() + other.area() - intersection

        return intersection / union if union > 0 else 0.0

    def contains_point(self, x: int, y: int) -> bool:
        """Check if a point is inside the bounding box"""
        return (
            self.x <= x <= self.x + self.width and
            self.y <= y <= self.y + self.height
        )

    def expand(self, margin: int) -> "BoundingBox":
        """
        Expand bounding box by margin

        Args:
            margin: Pixels to expand on all sides

        Returns:
            New expanded BoundingBox
        """
        return BoundingBox(
            x=max(0, self.x - margin),
            y=max(0, self.y - margin),
            width=self.width + 2 * margin,
            height=self.height + 2 * margin,
            page_number=self.page_number,
            confidence=self.confidence,
            label=self.label,
        )


class CoordinateMapper:
    """Handles coordinate transformations and bounding box operations"""

    @staticmethod
    def normalize_bbox(
        bbox: BoundingBox,
        source_width: int,
        source_height: int,
        target_width: int,
        target_height: int
    ) -> BoundingBox:
        """
        Normalize bounding box coordinates from source to target dimensions

        Args:
            bbox: Source bounding box
            source_width: Width of source image
            source_height: Height of source image
            target_width: Width of target image
            target_height: Height of target image

        Returns:
            BoundingBox with normalized coordinates
        """
        scale_x = target_width / source_width
        scale_y = target_height / source_height

        return BoundingBox(
            x=int(bbox.x * scale_x),
            y=int(bbox.y * scale_y),
            width=int(bbox.width * scale_x),
            height=int(bbox.height * scale_y),
            page_number=bbox.page_number,
            confidence=bbox.confidence,
            label=bbox.label,
        )

    @staticmethod
    def tile_to_page_coordinates(
        tile_bbox: BoundingBox,
        tile_x: int,
        tile_y: int
    ) -> BoundingBox:
        """
        Convert coordinates from tile space to page space

        Args:
            tile_bbox: Bounding box in tile coordinates
            tile_x: X offset of tile in page
            tile_y: Y offset of tile in page

        Returns:
            BoundingBox in page coordinates
        """
        return BoundingBox(
            x=tile_bbox.x + tile_x,
            y=tile_bbox.y + tile_y,
            width=tile_bbox.width,
            height=tile_bbox.height,
            page_number=tile_bbox.page_number,
            confidence=tile_bbox.confidence,
            label=tile_bbox.label,
        )

    @staticmethod
    def merge_overlapping_boxes(
        boxes: List[BoundingBox],
        iou_threshold: float = 0.5
    ) -> List[BoundingBox]:
        """
        Merge overlapping bounding boxes using IoU threshold

        Args:
            boxes: List of bounding boxes
            iou_threshold: IoU threshold for merging (0.0-1.0)

        Returns:
            List of merged bounding boxes
        """
        if not boxes:
            return []

        # Sort by confidence (descending)
        sorted_boxes = sorted(boxes, key=lambda b: b.confidence, reverse=True)

        merged = []
        used = set()

        for i, box1 in enumerate(sorted_boxes):
            if i in used:
                continue

            # Find overlapping boxes
            group = [box1]
            for j, box2 in enumerate(sorted_boxes[i + 1:], start=i + 1):
                if j in used:
                    continue

                if box1.intersection_over_union(box2) >= iou_threshold:
                    group.append(box2)
                    used.add(j)

            # Merge group into single box
            if len(group) == 1:
                merged.append(box1)
            else:
                merged_box = CoordinateMapper._merge_box_group(group)
                merged.append(merged_box)

        logger.debug(f"Merged {len(boxes)} boxes into {len(merged)}")

        return merged

    @staticmethod
    def _merge_box_group(boxes: List[BoundingBox]) -> BoundingBox:
        """
        Merge a group of bounding boxes into one

        Args:
            boxes: List of boxes to merge

        Returns:
            Single merged BoundingBox
        """
        if not boxes:
            raise ValueError("Cannot merge empty box list")

        # Find bounding rectangle
        min_x = min(b.x for b in boxes)
        min_y = min(b.y for b in boxes)
        max_x = max(b.x + b.width for b in boxes)
        max_y = max(b.y + b.height for b in boxes)

        # Average confidence
        avg_confidence = sum(b.confidence for b in boxes) / len(boxes)

        # Use label from highest confidence box
        label = max(boxes, key=lambda b: b.confidence).label

        return BoundingBox(
            x=min_x,
            y=min_y,
            width=max_x - min_x,
            height=max_y - min_y,
            page_number=boxes[0].page_number,
            confidence=avg_confidence,
            label=label,
        )

    @staticmethod
    def filter_by_area(
        boxes: List[BoundingBox],
        min_area: int = 100,
        max_area: Optional[int] = None
    ) -> List[BoundingBox]:
        """
        Filter bounding boxes by area

        Args:
            boxes: List of bounding boxes
            min_area: Minimum area in pixels
            max_area: Maximum area in pixels (None for no limit)

        Returns:
            Filtered list of bounding boxes
        """
        filtered = []
        for box in boxes:
            area = box.area()
            if area >= min_area:
                if max_area is None or area <= max_area:
                    filtered.append(box)

        logger.debug(f"Filtered {len(boxes)} boxes to {len(filtered)} by area")

        return filtered

    @staticmethod
    def sort_boxes_reading_order(boxes: List[BoundingBox]) -> List[BoundingBox]:
        """
        Sort bounding boxes in reading order (top-to-bottom, left-to-right)

        Args:
            boxes: List of bounding boxes

        Returns:
            Sorted list of bounding boxes
        """
        # Group by page
        by_page = {}
        for box in boxes:
            if box.page_number not in by_page:
                by_page[box.page_number] = []
            by_page[box.page_number].append(box)

        # Sort each page
        sorted_boxes = []
        for page_num in sorted(by_page.keys()):
            page_boxes = by_page[page_num]

            # Sort by y (top to bottom), then x (left to right)
            # Use tolerance for y to handle same-row items
            y_tolerance = 20
            page_boxes.sort(key=lambda b: (b.y // y_tolerance, b.x))

            sorted_boxes.extend(page_boxes)

        return sorted_boxes
