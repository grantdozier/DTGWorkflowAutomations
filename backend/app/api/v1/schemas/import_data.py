from pydantic import BaseModel
from typing import List, Dict, Any


class ImportValidationResult(BaseModel):
    valid_rows: int
    error_count: int
    errors: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]] = []


class ImportResult(BaseModel):
    success_count: int
    error_count: int
    errors: List[Dict[str, Any]]
    imported_ids: List[str] = []
