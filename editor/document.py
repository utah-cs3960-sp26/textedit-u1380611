"""
Document Model

Represents a text document independent of any view or widget.
Stores content, file path, modification state, cursor position, and undo history.
"""

from dataclasses import dataclass, field
from typing import Optional
from uuid import uuid4


@dataclass
class CursorPosition:
    """Stores cursor position within a document."""
    line: int = 1
    column: int = 1
    selection_start: Optional[int] = None
    selection_end: Optional[int] = None


@dataclass
class UndoEntry:
    """Single entry in the undo/redo stack."""
    content: str
    cursor_position: int


class Document:
    """
    Represents a text document independent of any view.
    
    Each document maintains its own:
    - Content
    - File path
    - Modification state
    - Cursor position
    - Undo/redo history
    """
    
    def __init__(self, content: str = "", file_path: Optional[str] = None):
        self._id: str = str(uuid4())
        self._content: str = content
        self._html_content: Optional[str] = None
        self._file_path: Optional[str] = file_path
        self._is_modified: bool = False
        self._cursor_position: CursorPosition = CursorPosition()
        self._undo_stack: list[UndoEntry] = []
        self._redo_stack: list[UndoEntry] = []
        self._scroll_position: tuple[int, int] = (0, 0)
        self._has_rich_formatting: bool = False
    
    @property
    def id(self) -> str:
        """Unique identifier for this document."""
        return self._id
    
    @property
    def content(self) -> str:
        """Get the document content."""
        return self._content
    
    @content.setter
    def content(self, value: str):
        """Set the document content."""
        self._content = value
    
    @property
    def html_content(self) -> Optional[str]:
        """Get the HTML content for rich text formatting."""
        return self._html_content
    
    @html_content.setter
    def html_content(self, value: Optional[str]):
        """Set the HTML content for rich text formatting."""
        self._html_content = value
    
    @property
    def file_path(self) -> Optional[str]:
        """Get the file path, or None if untitled."""
        return self._file_path
    
    @file_path.setter
    def file_path(self, path: Optional[str]):
        """Set the file path."""
        self._file_path = path
    
    @property
    def file_name(self) -> str:
        """Get the file name or 'Untitled'."""
        if self._file_path:
            from pathlib import Path
            return Path(self._file_path).name
        return "Untitled"
    
    @property
    def display_name(self) -> str:
        """Get display name (modification shown via blue dot in tab bar)."""
        return self.file_name
    
    @property
    def is_modified(self) -> bool:
        """Check if document has unsaved changes."""
        return self._is_modified
    
    @is_modified.setter
    def is_modified(self, value: bool):
        """Set the modification state."""
        self._is_modified = value
    
    @property
    def cursor_position(self) -> CursorPosition:
        """Get the cursor position."""
        return self._cursor_position
    
    @cursor_position.setter
    def cursor_position(self, pos: CursorPosition):
        """Set the cursor position."""
        self._cursor_position = pos
    
    @property
    def scroll_position(self) -> tuple[int, int]:
        """Get the scroll position (horizontal, vertical)."""
        return self._scroll_position
    
    @scroll_position.setter
    def scroll_position(self, pos: tuple[int, int]):
        """Set the scroll position."""
        self._scroll_position = pos
    
    @property
    def has_rich_formatting(self) -> bool:
        """Whether this document uses rich text formatting."""
        return self._has_rich_formatting

    @has_rich_formatting.setter
    def has_rich_formatting(self, value: bool):
        self._has_rich_formatting = value
    
    def mark_saved(self, file_path: Optional[str] = None):
        """Mark document as saved, optionally updating file path."""
        if file_path is not None:
            self._file_path = file_path
        self._is_modified = False
    
    def clear_undo_history(self):
        """Clear the undo/redo stacks."""
        self._undo_stack.clear()
        self._redo_stack.clear()
    
    def __eq__(self, other) -> bool:
        if isinstance(other, Document):
            return self._id == other._id
        return False
    
    def __hash__(self) -> int:
        return hash(self._id)
