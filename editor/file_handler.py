"""
File Handler Module

Handles all file I/O operations with proper error handling.
Separated from UI logic for testability and modularity.
"""

import mmap
import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional


class FileError(Enum):
    NONE = "none"
    READ_ERROR = "read_error"
    WRITE_ERROR = "write_error"
    PERMISSION_ERROR = "permission_error"
    NOT_FOUND = "not_found"
    CANCELLED = "cancelled"


@dataclass
class FileResult:
    success: bool
    content: Optional[str] = None
    error: FileError = FileError.NONE
    error_message: str = ""


@dataclass
class SaveResult:
    success: bool
    error: FileError = FileError.NONE
    error_message: str = ""


class FileHandler:
    """Handles file read/write operations with UTF-8 encoding."""
    
    _MMAP_THRESHOLD = 1_000_000  # 1 MB
    
    @staticmethod
    def read_file(file_path: str) -> FileResult:
        """
        Read a text file and return its contents.
        
        Uses mmap for files larger than 1 MB for better performance.
        
        Args:
            file_path: Path to the file to read.
            
        Returns:
            FileResult with success status, content, and any error info.
        """
        try:
            path = Path(file_path)
            if not path.exists():
                return FileResult(
                    success=False,
                    error=FileError.NOT_FOUND,
                    error_message=f"File not found: {file_path}"
                )
            
            file_size = path.stat().st_size
            if file_size == 0:
                return FileResult(success=True, content="")
            
            if file_size > FileHandler._MMAP_THRESHOLD:
                with open(path, 'rb') as f:
                    with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                        content = mm[:].decode('utf-8')
            else:
                content = path.read_text(encoding="utf-8")
            
            return FileResult(success=True, content=content)
            
        except PermissionError as e:
            return FileResult(
                success=False,
                error=FileError.PERMISSION_ERROR,
                error_message=f"Permission denied: {e}"
            )
        except (OSError, UnicodeDecodeError) as e:
            return FileResult(
                success=False,
                error=FileError.READ_ERROR,
                error_message=f"Error reading file: {e}"
            )
    
    @staticmethod
    def write_file(file_path: str, content: str) -> SaveResult:
        """
        Write content to a text file.
        
        Args:
            file_path: Path to save the file.
            content: Text content to write.
            
        Returns:
            SaveResult with success status and any error info.
        """
        try:
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            return SaveResult(success=True)
            
        except PermissionError as e:
            return SaveResult(
                success=False,
                error=FileError.PERMISSION_ERROR,
                error_message=f"Permission denied: {e}"
            )
        except OSError as e:
            return SaveResult(
                success=False,
                error=FileError.WRITE_ERROR,
                error_message=f"Error writing file: {e}"
            )
