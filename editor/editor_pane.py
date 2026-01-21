"""
Editor Pane Module

A container holding a tab bar and editor widget.
Manages multiple documents via tabs.
"""

from typing import Optional
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPlainTextEdit, QMessageBox
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QTextCursor

from editor.document import Document, CursorPosition
from editor.tab_bar import EditorTabBar
from editor.file_handler import FileHandler
from editor.line_number_editor import LineNumberedEditor


class EditorPane(QWidget):
    """
    A pane containing a tab bar and text editor.
    
    Manages multiple documents, each represented by a tab.
    """
    
    document_changed = Signal(object)
    document_modified = Signal(object, bool)
    pane_empty = Signal(object)
    tab_drag_started = Signal(int, object)
    close_tab_requested = Signal(object, int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._documents: list[Document] = []
        self._current_index: int = -1
        self._file_handler = FileHandler()
        
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self._tab_bar = EditorTabBar(self)
        self._tab_bar.setVisible(True)
        layout.addWidget(self._tab_bar)
        
        self._editor = LineNumberedEditor(self)
        self._editor.setLineWrapMode(LineNumberedEditor.LineWrapMode.WidgetWidth)
        layout.addWidget(self._editor)
        
        self._editor.textChanged.connect(self._on_text_changed)
        self._editor.cursorPositionChanged.connect(self._on_cursor_changed)
    
    def _connect_signals(self):
        """Connect tab bar signals."""
        self._tab_bar.currentChanged.connect(self._on_tab_changed)
        self._tab_bar.new_tab_requested.connect(self.add_new_document)
        self._tab_bar.tab_close_requested.connect(self._on_tab_close_requested)
        self._tab_bar.tabMoved.connect(self._on_tab_moved)
        self._tab_bar.external_drag_started.connect(self._on_external_drag_started)
    
    @property
    def tab_bar(self) -> EditorTabBar:
        """Get the tab bar widget."""
        return self._tab_bar
    
    @property
    def editor(self) -> QPlainTextEdit:
        """Get the editor widget."""
        return self._editor
    
    @property
    def documents(self) -> list[Document]:
        """Get all documents in this pane."""
        return self._documents.copy()
    
    @property
    def current_document(self) -> Optional[Document]:
        """Get the currently active document."""
        if 0 <= self._current_index < len(self._documents):
            return self._documents[self._current_index]
        return None
    
    @property
    def document_count(self) -> int:
        """Get the number of documents."""
        return len(self._documents)
    
    def add_document(self, document: Document, activate: bool = True) -> int:
        """Add a document to this pane."""
        self._save_current_state()
        
        self._documents.append(document)
        index = self._tab_bar.addTab(document.display_name)
        
        if activate:
            self._current_index = index
            self._tab_bar.setCurrentIndex(index)
            self._restore_document_state(document)
        
        return index
    
    def add_new_document(self) -> Document:
        """Create and add a new empty document."""
        doc = Document()
        self.add_document(doc)
        return doc
    
    def insert_document(self, index: int, document: Document, activate: bool = True) -> int:
        """Insert a document at a specific position."""
        self._save_current_state()
        
        index = max(0, min(index, len(self._documents)))
        self._documents.insert(index, document)
        self._tab_bar.insertTab(index, document.display_name)
        
        if activate:
            self._current_index = index
            self._tab_bar.setCurrentIndex(index)
            self._restore_document_state(document)
        
        return index
    
    def remove_document(self, document: Document) -> bool:
        """Remove a document from this pane."""
        if document not in self._documents:
            return False
        
        index = self._documents.index(document)
        self._documents.remove(document)
        self._tab_bar.removeTab(index)
        
        if len(self._documents) == 0:
            self._current_index = -1
            self.pane_empty.emit(self)
        else:
            new_index = self._tab_bar.currentIndex()
            self._current_index = new_index
            if 0 <= new_index < len(self._documents):
                self._restore_document_state(self._documents[new_index])
        
        return True
    
    def remove_document_at(self, index: int) -> Optional[Document]:
        """Remove and return the document at the given index."""
        if not (0 <= index < len(self._documents)):
            return None
        
        document = self._documents.pop(index)
        self._tab_bar.removeTab(index)
        
        if len(self._documents) == 0:
            self._current_index = -1
            self.pane_empty.emit(self)
        else:
            new_index = self._tab_bar.currentIndex()
            self._current_index = new_index
            if 0 <= new_index < len(self._documents):
                self._restore_document_state(self._documents[new_index])
        
        return document
    
    def get_document_at(self, index: int) -> Optional[Document]:
        """Get document at the given tab index."""
        if 0 <= index < len(self._documents):
            return self._documents[index]
        return None
    
    def set_current_document(self, document: Document) -> bool:
        """Switch to the given document."""
        if document in self._documents:
            index = self._documents.index(document)
            self._tab_bar.setCurrentIndex(index)
            return True
        return False
    
    def has_unsaved_changes(self) -> bool:
        """Check if any document has unsaved changes."""
        return any(doc.is_modified for doc in self._documents)
    
    def update_tab_title(self, document: Document):
        """Update the tab title for a document."""
        if document in self._documents:
            index = self._documents.index(document)
            self._tab_bar.setTabText(index, document.display_name)
            self._tab_bar.setTabModified(index, document.is_modified)
    
    def set_word_wrap(self, enabled: bool):
        """Toggle word wrap on the editor."""
        if enabled:
            self._editor.setLineWrapMode(LineNumberedEditor.LineWrapMode.WidgetWidth)
        else:
            self._editor.setLineWrapMode(LineNumberedEditor.LineWrapMode.NoWrap)
    
    def set_line_number_colors(self, bg: str, text: str, current_line: str, current_line_bg: str):
        """Set colors for the line number area."""
        self._editor.set_line_number_colors(bg, text, current_line, current_line_bg)
    
    def _save_current_state(self):
        """Save current editor state to the active document."""
        if self._current_index < 0 or self._current_index >= len(self._documents):
            return
        
        doc = self._documents[self._current_index]
        doc.content = self._editor.toPlainText()
        doc.html_content = self._editor.document().toHtml()
        
        cursor = self._editor.textCursor()
        doc.cursor_position = CursorPosition(
            line=cursor.blockNumber() + 1,
            column=cursor.columnNumber() + 1,
            selection_start=cursor.selectionStart() if cursor.hasSelection() else None,
            selection_end=cursor.selectionEnd() if cursor.hasSelection() else None
        )
        
        doc.scroll_position = (
            self._editor.horizontalScrollBar().value(),
            self._editor.verticalScrollBar().value()
        )
    
    def _restore_document_state(self, document: Document):
        """Restore editor state from a document."""
        self._editor.blockSignals(True)
        
        if document.html_content:
            self._editor.document().setHtml(document.html_content)
        else:
            self._editor.setPlainText(document.content)
        
        cursor = self._editor.textCursor()
        block = self._editor.document().findBlockByLineNumber(
            document.cursor_position.line - 1
        )
        if block.isValid():
            pos = block.position() + min(
                document.cursor_position.column - 1,
                block.length() - 1
            )
            cursor.setPosition(max(0, pos))
        self._editor.setTextCursor(cursor)
        
        self._editor.horizontalScrollBar().setValue(document.scroll_position[0])
        self._editor.verticalScrollBar().setValue(document.scroll_position[1])
        
        self._editor.blockSignals(False)
    
    def _on_tab_changed(self, index: int):
        """Handle tab selection change."""
        if index < 0 or index >= len(self._documents):
            return
        
        if self._current_index == index:
            return
        
        if self._current_index >= 0 and self._current_index < len(self._documents):
            self._save_current_state()
        
        self._current_index = index
        self._restore_document_state(self._documents[index])
        self.document_changed.emit(self._documents[index])
    
    def _on_text_changed(self):
        """Handle text changes in the editor."""
        doc = self.current_document
        if doc is None:
            return
        
        if not doc.is_modified:
            doc.is_modified = True
            self.update_tab_title(doc)
            self.document_modified.emit(doc, True)
    
    def _on_cursor_changed(self):
        """Handle cursor position changes."""
        pass
    
    def _on_tab_close_requested(self, index: int):
        """Handle tab close request - forward to container for proper handling."""
        self.close_tab_requested.emit(self, index)
    
    def _save_document(self, document: Document) -> bool:
        """Save a document to disk."""
        if document.file_path:
            self._save_current_state()
            result = self._file_handler.write_file(document.file_path, document.content)
            if result.success:
                document.mark_saved()
                self.update_tab_title(document)
                return True
            return False
        return False
    
    def _on_tab_moved(self, from_index: int, to_index: int):
        """Handle tab reordering within this pane."""
        if from_index == to_index:
            return
        
        if not (0 <= from_index < len(self._documents)):
            return
        if not (0 <= to_index < len(self._documents)):
            return
        
        doc = self._documents.pop(from_index)
        self._documents.insert(to_index, doc)
        
        self._current_index = self._tab_bar.currentIndex()
    
    def _on_external_drag_started(self, tab_index: int, global_pos):
        """Handle external drag (for split detection)."""
        self.tab_drag_started.emit(tab_index, self)
    
    def focus_editor(self):
        """Set focus to the editor widget."""
        self._editor.setFocus()
    
    def sync_from_editor(self):
        """Force sync current editor content to document."""
        self._save_current_state()
