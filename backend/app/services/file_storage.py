import os
import uuid
from pathlib import Path
from typing import Optional
from fastapi import UploadFile
import shutil

from app.core.config import settings


class FileStorage:
    """
    Handle local file storage for documents
    """

    def __init__(self):
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.plans_dir = self.upload_dir / "plans"
        self.specs_dir = self.upload_dir / "specs"

        # Ensure directories exist
        self.plans_dir.mkdir(parents=True, exist_ok=True)
        self.specs_dir.mkdir(parents=True, exist_ok=True)

    async def save_file(
        self,
        file: UploadFile,
        doc_type: str,
        project_id: str
    ) -> str:
        """
        Save uploaded file to disk

        Args:
            file: FastAPI UploadFile object
            doc_type: Type of document (plan, spec)
            project_id: Project ID for organization

        Returns:
            Relative file path
        """
        # Determine directory based on doc type
        if doc_type == "plan":
            target_dir = self.plans_dir
        elif doc_type == "spec":
            target_dir = self.specs_dir
        else:
            target_dir = self.upload_dir

        # Create project subdirectory
        project_dir = target_dir / project_id
        project_dir.mkdir(parents=True, exist_ok=True)

        # Generate unique filename
        file_extension = Path(file.filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = project_dir / unique_filename

        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Return relative path from upload dir
        relative_path = file_path.relative_to(self.upload_dir)
        return str(relative_path)

    def get_file_path(self, relative_path: str) -> Path:
        """
        Get absolute file path from relative path

        Args:
            relative_path: Relative path from upload dir

        Returns:
            Absolute file path
        """
        return self.upload_dir / relative_path

    def delete_file(self, relative_path: str) -> bool:
        """
        Delete file from disk

        Args:
            relative_path: Relative path from upload dir

        Returns:
            True if deleted, False if file doesn't exist
        """
        file_path = self.get_file_path(relative_path)

        if file_path.exists():
            file_path.unlink()
            return True

        return False

    def file_exists(self, relative_path: str) -> bool:
        """
        Check if file exists

        Args:
            relative_path: Relative path from upload dir

        Returns:
            True if file exists
        """
        file_path = self.get_file_path(relative_path)
        return file_path.exists()

    def get_file_size(self, relative_path: str) -> Optional[int]:
        """
        Get file size in bytes

        Args:
            relative_path: Relative path from upload dir

        Returns:
            File size in bytes, or None if file doesn't exist
        """
        file_path = self.get_file_path(relative_path)

        if file_path.exists():
            return file_path.stat().st_size

        return None


# Singleton instance
file_storage = FileStorage()
