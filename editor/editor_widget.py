"""
Editor Widget Module

Provides the central text editing widget with state management.
Built on QPlainTextEdit for future extensibility.
"""

from typing import Optional
from PySide6.QtWidgets import QPlainTextEdit
from PySide6.QtCore import Signal
from PySide6.QtGui import QTextCursor


class EditorWidget(QPlainTextEdit):
    """
    Central text editing widget with document state management.
    
    Signals:
        cursor_position_changed: Emitted when cursor moves (line, column).
        modified_state_changed: Emitted when document modified state changes.
    """
    
    cursor_position_changed = Signal(int, int)
    modified_state_changed = Signal(bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._current_file_path: Optional[str] = None
        self._is_modified: bool = False
        
        self.cursorPositionChanged.connect(self._on_cursor_position_changed)
        self.textChanged.connect(self._on_text_changed)
        self.document().modificationChanged.connect(self._on_modification_changed)
    
    @property
    def current_file_path(self) -> Optional[str]:
        """Get the current file path, or None if untitled."""
        return self._current_file_path
    
    @current_file_path.setter
    def current_file_path(self, path: Optional[str]):
        """Set the current file path."""
        self._current_file_path = path
    
    @property
    def is_modified(self) -> bool:
        """Check if the document has unsaved changes."""
        return self.document().isModified()
    
    @property
    def file_name(self) -> str:
        """Get the current file name or 'Untitled'."""
        if self._current_file_path:
            from pathlib import Path
            return Path(self._current_file_path).name
        return "Untitled"
    
    def get_cursor_position(self) -> tuple[int, int]:
        """
        Get current cursor position.
        
        Returns:
            Tuple of (line, column), both 1-indexed.
        """
        cursor = self.textCursor()
        line = cursor.blockNumber() + 1
        column = cursor.columnNumber() + 1
        return line, column
    
    def set_content(self, content: str, file_path: Optional[str] = None):
        """
        Set the editor content, typically from file load.
        
        Args:
            content: Text content to set.
            file_path: Associated file path, or None for new document.
        """
        self.setPlainText(content)
        self._current_file_path = file_path
        self.document().setModified(False)
        self.document().clearUndoRedoStacks()
        self._move_cursor_to_start()
    
    def get_content(self) -> str:
        """Get the current editor content."""
        return self.toPlainText()
    
    def new_document(self):
        """Clear editor for a new document."""
        self.clear()
        self._current_file_path = None
        self.document().setModified(False)
        self.document().clearUndoRedoStacks()
        self._move_cursor_to_start()
    
    def mark_as_saved(self, file_path: str):
        """
        Mark document as saved to a path.
        
        Args:
            file_path: The path where the file was saved.
        """
        self._current_file_path = file_path
        self.document().setModified(False)
    
    def set_word_wrap(self, enabled: bool):
        """Toggle word wrap mode."""
        if enabled:
            self.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        else:
            self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
    
    def is_word_wrap_enabled(self) -> bool:
        """Check if word wrap is currently enabled."""
        return self.lineWrapMode() == QPlainTextEdit.LineWrapMode.WidgetWidth
    
    def _move_cursor_to_start(self):
        """Move cursor to the beginning of the document."""
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        self.setTextCursor(cursor)
    
    def _on_cursor_position_changed(self):
        """Handle cursor position changes."""
        line, column = self.get_cursor_position()
        self.cursor_position_changed.emit(line, column)
    
    def _on_text_changed(self):
        """Handle text content changes."""
        pass
    
    def _on_modification_changed(self, modified: bool):
        """Handle document modification state changes."""
        self.modified_state_changed.emit(modified)
