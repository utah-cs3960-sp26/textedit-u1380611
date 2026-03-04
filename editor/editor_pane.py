"""
Editor Pane Module

A container holding a tab bar and editor widget.
Manages multiple documents via tabs.
"""

from typing import Optional
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPlainTextEdit, QMessageBox, QScrollBar
from PySide6.QtCore import Signal, Qt, QTimer, QCoreApplication
from PySide6.QtGui import QTextCursor, QTextDocument
from PySide6.QtWidgets import QPlainTextDocumentLayout

from editor.document import Document, CursorPosition
from editor.tab_bar import EditorTabBar
from editor.file_handler import FileHandler
from editor.line_number_editor import LineNumberedEditor
from editor.virtual_document import VirtualDocumentController, LineIndex


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
        self._content_dirty: bool = False
        self._word_wrap_preference: bool = True
        self._virtual_controller = VirtualDocumentController(self)
        
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
        
        # Editor + global scrollbar (for virtualised large files)
        editor_row = QHBoxLayout()
        editor_row.setContentsMargins(0, 0, 0, 0)
        editor_row.setSpacing(0)
        
        self._editor = LineNumberedEditor(self)
        self._editor.setLineWrapMode(LineNumberedEditor.LineWrapMode.WidgetWidth)
        editor_row.addWidget(self._editor)
        
        self._global_scrollbar = QScrollBar(Qt.Orientation.Vertical, self)
        self._global_scrollbar.hide()
        editor_row.addWidget(self._global_scrollbar)
        
        layout.addLayout(editor_row)
        
        self._editor.textChanged.connect(self._on_text_changed)
        self._editor.cursorPositionChanged.connect(self._on_cursor_changed)
        self._editor.document().modificationChanged.connect(self._on_modification_changed)
    
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
        self._word_wrap_preference = enabled
        # Don't enable word wrap for large documents — layout is too expensive
        doc = self.current_document
        if enabled and doc and len(doc.content) > self._LARGE_DOC_THRESHOLD:
            return
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
        
        # Virtualised documents: save virtual state, not editor content
        if self._virtual_controller.active:
            vc = self._virtual_controller
            cursor = self._editor.textCursor()
            local_line = cursor.blockNumber()
            global_line = vc.window_start + local_line
            doc.cursor_position = CursorPosition(
                line=global_line + 1,
                column=cursor.columnNumber() + 1,
            )
            doc.scroll_position = (self._editor.horizontalScrollBar().value(), 0)
            doc._virtual_state = vc.save_state()
            # Don't cache qt_document for virtual docs – it's a small window
            doc.qt_document = None
            return
        
        # Only copy content from editor when text has actually changed,
        # avoiding a full toPlainText() copy (253MB+ for large files) on every tab switch
        if self._content_dirty:
            doc.content = self._editor.toPlainText()
            self._content_dirty = False
        # Only generate HTML for documents with rich text formatting.
        # For plain text, toHtml() can produce output 3-5x larger than the text,
        # causing severe memory bloat for large files.
        if doc.has_rich_formatting or doc.html_content is not None:
            doc.html_content = self._editor.document().toHtml()
        else:
            doc.html_content = None
        
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
        
        # Cache the live QTextDocument so tab switching avoids rebuilding all blocks.
        # We detach it from the editor and store it on the Document model.
        try:
            doc.qt_document = self._editor.document()
        except RuntimeError:
            doc.qt_document = None
    
    _LARGE_DOC_THRESHOLD = 1_000_000  # 1MB
    _VIRTUAL_THRESHOLD = 5_000_000   # 5MB – use virtualised loading above this
    _CHUNK_SIZE = 2_000_000  # 2MB per chunk for chunked loading
    
    def _is_virtual(self, document: Document) -> bool:
        """Whether *document* should use virtualised (viewport-only) loading."""
        if document.html_content:
            return False
        return len(document.content) > self._VIRTUAL_THRESHOLD
    
    def _restore_document_state(self, document: Document):
        """Restore editor state from a document.
        
        Uses cached QTextDocument when available to avoid the expensive
        rebuild of QTextBlock structures on every tab switch.
        For very large files (>5MB), uses virtualised viewport loading.
        For moderately large files, uses chunked insertion.
        """
        # Detach any active virtualisation first
        self._virtual_controller.detach()
        self._editor._virtual_wheel_handler = None
        
        # Block editor signals during restoration
        self._editor.blockSignals(True)
        
        # Auto-disable word wrap for large documents before loading content.
        content_size = len(document.html_content or document.content)
        if content_size > self._LARGE_DOC_THRESHOLD:
            self._editor.setLineWrapMode(LineNumberedEditor.LineWrapMode.NoWrap)
        elif self._word_wrap_preference:
            self._editor.setLineWrapMode(LineNumberedEditor.LineWrapMode.WidgetWidth)
        else:
            self._editor.setLineWrapMode(LineNumberedEditor.LineWrapMode.NoWrap)
        
        # ── Virtualised path for very large files ──
        if self._is_virtual(document):
            self._restore_virtual(document)
            return
        
        if document.qt_document is not None:
            # Fast path: swap in the cached QTextDocument directly.
            try:
                old_doc = self._editor.document()
                document.qt_document.blockSignals(True)
                self._editor.setDocument(document.qt_document)
                try:
                    if old_doc is not None and old_doc.parent() == self._editor:
                        old_doc.setParent(None)
                except RuntimeError:
                    pass
            except RuntimeError:
                document.qt_document = None
                new_doc = self._new_qt_document()
                new_doc.blockSignals(True)
                self._editor.setDocument(new_doc)
                if document.html_content:
                    new_doc.setHtml(document.html_content)
                else:
                    new_doc.setPlainText(document.content)
        elif document.html_content:
            new_doc = self._new_qt_document()
            new_doc.blockSignals(True)
            self._editor.setDocument(new_doc)
            new_doc.setHtml(document.html_content)
        elif content_size > self._LARGE_DOC_THRESHOLD:
            new_doc = self._new_qt_document()
            new_doc.blockSignals(True)
            self._editor.setDocument(new_doc)
            self._load_content_chunked(document.content)
        else:
            new_doc = self._new_qt_document()
            new_doc.blockSignals(True)
            self._editor.setDocument(new_doc)
            new_doc.setPlainText(document.content)
        
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
        
        if document.qt_document is None:
            self._editor.document().clearUndoRedoStacks()
            self._editor.document().setUndoRedoEnabled(True)
        
        self._editor.document().setModified(document.is_modified)
        
        # Reconnect modificationChanged since we swapped documents
        self._editor.document().blockSignals(False)
        try:
            self._editor.document().modificationChanged.disconnect(self._on_modification_changed)
        except RuntimeError:
            pass
        self._editor.document().modificationChanged.connect(self._on_modification_changed)
        
        self._editor.blockSignals(False)
        self._content_dirty = False
    
    def _restore_virtual(self, document: Document):
        """Restore a very large document using virtualised viewport loading."""
        from concurrent.futures import ThreadPoolExecutor
        
        # Set up a fresh QTextDocument and show a "Loading…" placeholder immediately
        new_doc = self._new_qt_document()
        new_doc.blockSignals(True)
        self._editor.setDocument(new_doc)
        new_doc.setPlainText("Loading large file…")
        new_doc.blockSignals(False)
        self._editor.blockSignals(False)
        
        # Build (or reuse cached) line index
        cached_index = getattr(document, '_line_index', None)
        if cached_index is not None:
            self._finish_virtual_restore(document, cached_index)
            return
        
        # Build index in a background thread so the GUI thread isn't blocked
        self._pending_virtual_doc = document
        
        def _build_index(content):
            return LineIndex(content)
        
        pool = ThreadPoolExecutor(max_workers=1)
        future = pool.submit(_build_index, document.content)
        
        def _on_index_ready():
            if not future.done():
                QTimer.singleShot(16, _on_index_ready)
                return
            pool.shutdown(wait=False)
            # Ensure the document hasn't been switched away during build
            if self._pending_virtual_doc is not document:
                return
            self._pending_virtual_doc = None
            index = future.result()
            document._line_index = index
            self._finish_virtual_restore(document, index)
        
        QTimer.singleShot(16, _on_index_ready)
    
    def _finish_virtual_restore(self, document: Document, index: LineIndex):
        """Complete virtualised restore once the LineIndex is ready."""
        self._editor.blockSignals(True)
        
        new_doc = self._new_qt_document()
        new_doc.blockSignals(True)
        self._editor.setDocument(new_doc)
        
        # Attach virtual controller
        self._virtual_controller.attach(
            self._editor, self._global_scrollbar, document.content, index
        )
        self._editor._virtual_wheel_handler = self._virtual_controller.handle_wheel
        
        # Restore previous virtualisation state if available
        vstate = getattr(document, '_virtual_state', None)
        if vstate:
            self._virtual_controller.restore_state(vstate)
        
        # Restore cursor
        line0 = document.cursor_position.line - 1
        col0 = document.cursor_position.column - 1
        self._virtual_controller.set_cursor_global(line0, col0)
        
        new_doc.setModified(document.is_modified)
        new_doc.blockSignals(False)
        
        try:
            new_doc.modificationChanged.disconnect(self._on_modification_changed)
        except RuntimeError:
            pass
        new_doc.modificationChanged.connect(self._on_modification_changed)
        
        self._editor.blockSignals(False)
        self._content_dirty = False
    
    def _new_qt_document(self) -> QTextDocument:
        """Create a fresh QTextDocument with QPlainTextDocumentLayout.
        
        QPlainTextEdit requires QPlainTextDocumentLayout; a bare QTextDocument
        uses QTextDocumentLayout which triggers warnings and layout errors.
        """
        doc = QTextDocument()
        doc.setDocumentLayout(QPlainTextDocumentLayout(doc))
        doc.setUndoRedoEnabled(False)
        return doc

    def _load_content_chunked(self, content: str):
        """Load large content in chunks with updates disabled to reduce stall time."""
        doc = self._editor.document()
        doc.setUndoRedoEnabled(False)
        self._editor.setUpdatesEnabled(False)
        
        # Start with empty document
        self._editor.setPlainText("")
        cursor = QTextCursor(doc)
        cursor.movePosition(QTextCursor.MoveOperation.End)
        
        offset = 0
        total = len(content)
        while offset < total:
            end = min(offset + self._CHUNK_SIZE, total)
            cursor.insertText(content[offset:end])
            offset = end
            # Let Qt process pending events between chunks to keep UI responsive
            QCoreApplication.processEvents()
        
        doc.setUndoRedoEnabled(True)
        self._editor.setUpdatesEnabled(True)
    
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
        if self._virtual_controller.active:
            return  # edits in virtual mode are not propagated to the raw content
        self._content_dirty = True
        doc = self.current_document
        if doc is None:
            return
        doc.invalidate_search_content()
        
        # Don't set modified=True if Qt's internal modification flag is False
        # (this happens during undo/redo back to clean state)
        if not self._editor.document().isModified():
            return
        
        if not doc.is_modified:
            doc.is_modified = True
            self.update_tab_title(doc)
            self.document_modified.emit(doc, True)
    
    def _on_cursor_changed(self):
        """Handle cursor position changes."""
        pass
    
    def _on_modification_changed(self, is_modified: bool):
        """Handle document modification state changes from Qt's undo/redo system.
        
        When undo/redo brings the document back to its saved state,
        Qt's modificationChanged signal fires with is_modified=False.
        """
        doc = self.current_document
        if doc is None:
            return
        
        doc.is_modified = is_modified
        self.update_tab_title(doc)
        self.document_modified.emit(doc, is_modified)
    
    def _on_tab_close_requested(self, index: int):
        """Handle tab close request - forward to container for proper handling."""
        self.close_tab_requested.emit(self, index)
    
    def _save_document(self, document: Document) -> bool:
        """Save a document to disk."""
        if document.file_path:
            self._save_current_state()
            content_to_save = document.html_content if document.html_content else document.content
            result = self._file_handler.write_file(document.file_path, content_to_save)
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
