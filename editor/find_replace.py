"""
Find and Replace Module

Provides find/replace functionality for single documents and across open tabs.
"""

import bisect
import re
import threading
from dataclasses import dataclass
from typing import Optional, List, Tuple
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QLabel, QWidget, QCheckBox, QGroupBox, QTreeWidget, QTreeWidgetItem,
    QSplitter, QPlainTextEdit, QMessageBox, QTextEdit
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import (
    QTextCursor, QTextCharFormat, QColor, QBrush, QTextDocument
)

from editor.document import Document


@dataclass
class SearchMatch:
    """Represents a single search match."""
    start: int
    end: int
    line_number: int
    line_text: str


@dataclass
class DocumentMatches:
    """Matches within a single document."""
    document: "Document"
    matches: List[SearchMatch]
    
    @property
    def count(self) -> int:
        return len(self.matches)


class FindReplaceEngine:
    """
    Core find/replace logic, independent of UI.
    
    Works with plain text content strings.
    """
    
    @staticmethod
    def find_all(content: str, query: str, case_sensitive: bool = False) -> List[SearchMatch]:
        """
        Find all occurrences of query in content.
        
        Args:
            content: Text to search in.
            query: Text to search for.
            case_sensitive: Whether to match case.
            
        Returns:
            List of SearchMatch objects.
        """
        if not query:
            return []
        
        matches = []
        
        # Build line_starts by scanning for newlines instead of content.split('\n')
        # which would create millions of string objects for large files
        line_starts = [0]
        idx = 0
        while True:
            idx = content.find('\n', idx)
            if idx == -1:
                break
            line_starts.append(idx + 1)
            idx += 1
        
        content_len = len(content)
        
        if case_sensitive:
            pos = 0
            qlen = len(query)
            while True:
                idx = content.find(query, pos)
                if idx == -1:
                    break
                line_num = bisect.bisect_right(line_starts, idx) - 1
                line_start = line_starts[line_num]
                line_end = line_starts[line_num + 1] - 1 if line_num + 1 < len(line_starts) else content_len
                matches.append(SearchMatch(
                    start=idx, end=idx + qlen,
                    line_number=line_num + 1,
                    line_text=content[line_start:line_end]
                ))
                pos = idx + 1
        else:
            # Use re.finditer with IGNORECASE to avoid content.lower() copy
            pattern = re.compile(re.escape(query), re.IGNORECASE)
            for m in pattern.finditer(content):
                idx = m.start()
                line_num = bisect.bisect_right(line_starts, idx) - 1
                line_start = line_starts[line_num]
                line_end = line_starts[line_num + 1] - 1 if line_num + 1 < len(line_starts) else content_len
                matches.append(SearchMatch(
                    start=m.start(), end=m.end(),
                    line_number=line_num + 1,
                    line_text=content[line_start:line_end]
                ))
        
        return matches
    
    @staticmethod
    def find_positions(content: str, query: str, case_sensitive: bool = False,
                       generation: int = 0, generation_ref: list | None = None) -> List[Tuple[int, int]]:
        """Fast search returning only (start, end) position tuples. No line info.

        If *generation_ref* is provided, the search checks
        ``generation_ref[0] == generation`` periodically and aborts early
        (returning partial results) when it becomes stale.
        """
        if not query:
            return []

        # How often to check cancellation (every N matches)
        _CANCEL_CHECK = 5000

        if case_sensitive:
            positions: List[Tuple[int, int]] = []
            pos = 0
            qlen = len(query)
            while True:
                idx = content.find(query, pos)
                if idx == -1:
                    break
                positions.append((idx, idx + qlen))
                pos = idx + 1
                if generation_ref is not None and len(positions) % _CANCEL_CHECK == 0:
                    if generation_ref[0] != generation:
                        return positions
            return positions
        else:
            pattern = re.compile(re.escape(query), re.IGNORECASE)
            positions = []
            for m in pattern.finditer(content):
                positions.append((m.start(), m.end()))
                if generation_ref is not None and len(positions) % _CANCEL_CHECK == 0:
                    if generation_ref[0] != generation:
                        return positions
            return positions
    
    @staticmethod
    def replace_all(content: str, query: str, replacement: str, 
                    case_sensitive: bool = False) -> Tuple[str, int]:
        """
        Replace all occurrences of query with replacement.
        
        Args:
            content: Text to search in.
            query: Text to search for.
            replacement: Text to replace with.
            case_sensitive: Whether to match case.
            
        Returns:
            Tuple of (new_content, replacement_count).
        """
        if not query:
            return content, 0
        
        if case_sensitive:
            count = content.count(query)
            if count == 0:
                return content, 0
            return content.replace(query, replacement), count
        
        # Use re.subn for case-insensitive to avoid content.lower() copy
        pattern = re.compile(re.escape(query), re.IGNORECASE)
        new_content, count = pattern.subn(lambda m: replacement, content)
        if count == 0:
            return content, 0
        return new_content, count


class FindReplaceDialog(QDialog):
    """
    Dialog for find and replace in the current document.
    Search runs in a background thread so the editor stays interactive.
    """
    
    _SEARCH_DEBOUNCE_MS = 300
    _POLL_MS = 30  # how often to check if the bg search finished

    def __init__(self, editor: QPlainTextEdit, parent=None, content_provider=None):
        super().__init__(parent)
        self._editor = editor
        self._content_provider = content_provider
        self._matches: List[Tuple[int, int]] = []
        self._match_starts: List[int] = []  # cached for bisect lookups
        self._current_match_index: int = -1
        self._highlight_format = QTextCharFormat()
        self._highlight_format.setBackground(QBrush(QColor(255, 255, 0, 80)))
        self._current_format = QTextCharFormat()
        self._current_format.setBackground(QBrush(QColor(255, 165, 0, 150)))
        self._extra_selections = []
        
        # Background search state
        self._search_generation: int = 0      # incremented on each new search
        self._generation_ref: list = [0]      # mutable ref shared with bg thread
        self._bg_thread: threading.Thread | None = None
        self._bg_result: List[Tuple[int, int]] | None = None
        self._bg_done = threading.Event()
        self._searching = False
        self._replace_poll_timer: QTimer | None = None
        self._replace_gen: int = 0
        
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(self._SEARCH_DEBOUNCE_MS)
        self._search_timer.timeout.connect(self._do_deferred_search)
        
        self._poll_timer = QTimer(self)
        self._poll_timer.setInterval(self._POLL_MS)
        self._poll_timer.timeout.connect(self._poll_search)
        
        self._scroll_highlight_timer = QTimer(self)
        self._scroll_highlight_timer.setSingleShot(True)
        self._scroll_highlight_timer.setInterval(16)
        self._scroll_highlight_timer.timeout.connect(self._update_highlights)
        
        self._setup_ui()
        self._editor.updateRequest.connect(self._on_viewport_scrolled)
        self.setWindowTitle("Find and Replace")
        self.setMinimumWidth(400)
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        find_layout = QHBoxLayout()
        find_layout.addWidget(QLabel("Find:"))
        self._find_edit = QLineEdit()
        self._find_edit.textChanged.connect(self._on_query_changed)
        self._find_edit.returnPressed.connect(self._find_next)
        find_layout.addWidget(self._find_edit, 1)
        layout.addLayout(find_layout)
        
        replace_layout = QHBoxLayout()
        replace_layout.addWidget(QLabel("Replace:"))
        self._replace_edit = QLineEdit()
        replace_layout.addWidget(self._replace_edit, 1)
        layout.addLayout(replace_layout)
        
        options_layout = QHBoxLayout()
        self._case_checkbox = QCheckBox("Match Case")
        self._case_checkbox.stateChanged.connect(self._on_query_changed)
        options_layout.addWidget(self._case_checkbox)
        options_layout.addStretch()
        layout.addLayout(options_layout)
        
        self._status_label = QLabel("Enter search text")
        layout.addWidget(self._status_label)
        
        btn_layout = QHBoxLayout()
        
        self._find_prev_btn = QPushButton("Find Previous")
        self._find_prev_btn.clicked.connect(self._find_prev)
        btn_layout.addWidget(self._find_prev_btn)
        
        self._find_next_btn = QPushButton("Find Next")
        self._find_next_btn.clicked.connect(self._find_next)
        btn_layout.addWidget(self._find_next_btn)
        
        layout.addLayout(btn_layout)
        
        replace_btn_layout = QHBoxLayout()
        
        self._replace_btn = QPushButton("Replace")
        self._replace_btn.clicked.connect(self._replace_current)
        replace_btn_layout.addWidget(self._replace_btn)
        
        self._replace_all_btn = QPushButton("Replace All")
        self._replace_all_btn.clicked.connect(self._replace_all)
        replace_btn_layout.addWidget(self._replace_all_btn)
        
        layout.addLayout(replace_btn_layout)
        
        close_layout = QHBoxLayout()
        close_layout.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        close_layout.addWidget(close_btn)
        layout.addLayout(close_layout)
    
    def show_find(self):
        """Show the dialog in find mode."""
        cursor = self._editor.textCursor()
        if cursor.hasSelection():
            self._find_edit.setText(cursor.selectedText())
        self._find_edit.setFocus()
        self._find_edit.selectAll()
        self.show()
        # Run search immediately when dialog opens (no debounce)
        self._do_deferred_search()
    
    def show_replace(self):
        """Show the dialog in replace mode."""
        cursor = self._editor.textCursor()
        if cursor.hasSelection():
            self._find_edit.setText(cursor.selectedText())
        self._find_edit.setFocus()
        self._find_edit.selectAll()
        self.show()
        # Run search immediately when dialog opens (no debounce)
        self._do_deferred_search()
    
    @property
    def query(self) -> str:
        return self._find_edit.text()
    
    @property
    def replacement(self) -> str:
        return self._replace_edit.text()
    
    @property
    def case_sensitive(self) -> bool:
        return self._case_checkbox.isChecked()
    
    def _on_query_changed(self, *args):
        """Debounce search: restart timer on each keystroke."""
        if not self.query:
            self._search_timer.stop()
            self._cancel_bg_search()
            self._matches = []
            self._match_starts = []
            self._current_match_index = -1
            self._status_label.setText("Enter search text")
            self._clear_highlights()
            return
        self._status_label.setText("Searching…")
        self._search_timer.start()
    
    def _do_deferred_search(self):
        """Kick off a background search after the debounce delay."""
        self._search_timer.stop()
        self._start_bg_search()
    
    def _ensure_search_complete(self):
        """If a search is pending or running, block until it finishes."""
        if self._search_timer.isActive():
            self._search_timer.stop()
            self._start_bg_search()
        # If a background thread exists, wait for it and collect results
        if self._bg_thread is not None:
            self._bg_done.wait()
            self._poll_search()  # collect result
    
    def _get_content(self):
        """Get searchable content, using cache when available."""
        if self._content_provider:
            cached = self._content_provider()
            if cached is not None:
                return cached
        return self._editor.toPlainText()

    # ── Background search machinery ──────────────────────────────────

    def _cancel_bg_search(self):
        """Invalidate any in-progress background search."""
        self._search_generation += 1
        self._generation_ref[0] = self._search_generation
        self._poll_timer.stop()
        self._searching = False

    def _start_bg_search(self):
        """Launch find_positions in a background thread."""
        self._cancel_bg_search()
        query = self.query
        if not query:
            self._apply_search_results([])
            return

        content = self._get_content()
        case_sensitive = self.case_sensitive
        gen = self._search_generation
        self._generation_ref[0] = gen
        self._bg_done.clear()
        self._bg_result = None
        self._searching = True
        self._status_label.setText("Searching…")

        gen_ref = self._generation_ref

        def _worker():
            result = FindReplaceEngine.find_positions(
                content, query, case_sensitive,
                generation=gen, generation_ref=gen_ref,
            )
            if gen_ref[0] == gen:
                self._bg_result = result
            self._bg_done.set()

        self._bg_thread = threading.Thread(target=_worker, daemon=True)
        self._bg_thread.start()
        self._poll_timer.start()

    def _poll_search(self):
        """Check whether the background search has finished."""
        if not self._bg_done.is_set():
            return
        self._poll_timer.stop()
        self._searching = False
        result = self._bg_result
        self._bg_result = None
        self._bg_thread = None
        if result is None:
            return  # generation was superseded
        self._apply_search_results(result)

    def _apply_search_results(self, positions: List[Tuple[int, int]]):
        """Apply results produced by the background thread to the UI."""
        self._matches = positions
        self._match_starts = [m[0] for m in positions]
        if not self._matches:
            self._current_match_index = -1
            if self.query:
                self._status_label.setText("No matches found")
            else:
                self._status_label.setText("Enter search text")
        else:
            cursor_pos = self._editor.textCursor().position()
            self._current_match_index = 0
            idx = bisect.bisect_left(self._match_starts, cursor_pos)
            if idx < len(self._matches):
                self._current_match_index = idx
            self._update_status()
        self._update_highlights()
    
    def _update_status(self):
        """Update the status label."""
        if self._matches:
            self._status_label.setText(
                f"Match {self._current_match_index + 1} of {len(self._matches)}"
            )
    
    _HIGHLIGHT_ALL_THRESHOLD = 500

    def _update_highlights(self):
        """Update highlighting — only visible matches for large result sets."""
        self._clear_highlights()

        if not self._matches:
            return

        cur_match = None
        if 0 <= self._current_match_index < len(self._matches):
            cur_match = self._matches[self._current_match_index]

        if len(self._matches) > self._HIGHLIGHT_ALL_THRESHOLD:
            visible_start, visible_end = self._get_visible_range()
            if visible_start is not None:
                lo = bisect.bisect_left(self._match_starts, visible_start)
                hi = bisect.bisect_right(self._match_starts, visible_end)
                lo = max(0, lo - 2)
                hi = min(len(self._matches), hi + 2)
                matches_to_highlight = self._matches[lo:hi]
            else:
                matches_to_highlight = self._matches[:50]
        else:
            matches_to_highlight = self._matches

        doc = self._editor.document()
        selections = []
        highlight_fmt = self._highlight_format
        current_fmt = self._current_format

        for start, end in matches_to_highlight:
            cursor = QTextCursor(doc)
            cursor.setPosition(start)
            cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)

            sel = QTextEdit.ExtraSelection()
            sel.cursor = cursor
            sel.format = current_fmt if (start, end) == cur_match else highlight_fmt
            selections.append(sel)

        self._extra_selections = selections
        if hasattr(self._editor, 'set_search_selections'):
            self._editor.set_search_selections(selections)
        else:
            self._editor.setExtraSelections(selections)
    
    def _get_visible_range(self):
        """Get the character position range visible in the viewport."""
        first_block = self._editor.firstVisibleBlock()
        if not first_block.isValid():
            return None, None
        visible_start = first_block.position()
        
        viewport_height = self._editor.viewport().height()
        if viewport_height <= 0:
            return None, None
        
        block = first_block
        visible_end = visible_start
        while block.isValid():
            geo = self._editor.blockBoundingGeometry(block).translated(self._editor.contentOffset())
            if geo.top() > viewport_height:
                break
            visible_end = block.position() + block.length()
            block = block.next()
        
        return visible_start, visible_end
    
    def _clear_highlights(self):
        """Clear all search highlights."""
        if hasattr(self._editor, 'clear_search_selections'):
            self._editor.clear_search_selections()
        else:
            self._editor.setExtraSelections([])
        self._extra_selections = []
    
    def _find_next(self):
        """Navigate to the next match."""
        self._ensure_search_complete()
        if not self._matches:
            return
        
        self._current_match_index = (self._current_match_index + 1) % len(self._matches)
        self._goto_current_match()
        self._update_highlights()
        self._update_status()
    
    def _find_prev(self):
        """Navigate to the previous match."""
        self._ensure_search_complete()
        if not self._matches:
            return
        
        self._current_match_index = (self._current_match_index - 1) % len(self._matches)
        self._goto_current_match()
        self._update_highlights()
        self._update_status()
    
    def _goto_current_match(self):
        """Move cursor to current match and select it."""
        if self._current_match_index < 0 or self._current_match_index >= len(self._matches):
            return
        
        start, end = self._matches[self._current_match_index]
        cursor = self._editor.textCursor()
        cursor.setPosition(start)
        cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
        self._editor.setTextCursor(cursor)
        self._editor.centerCursor()
    
    def _replace_current(self):
        """Replace the current match."""
        self._ensure_search_complete()
        if not self._matches or self._current_match_index < 0:
            return
        
        start, end = self._matches[self._current_match_index]
        cursor = self._editor.textCursor()
        
        if cursor.hasSelection():
            sel_start = cursor.selectionStart()
            sel_end = cursor.selectionEnd()
            if sel_start == start and sel_end == end:
                cursor.insertText(self.replacement)
                self._start_bg_search()
                return
        
        self._goto_current_match()
    
    _REPLACE_CHUNK = 500_000  # characters per chunk when rebuilding document

    def _replace_all(self):
        """Replace all matches.

        For bulk replacements (>1000 matches) on large documents, the string
        replacement is done in a background thread and the document is rebuilt
        in chunks so the GUI stays responsive.
        """
        self._ensure_search_complete()
        if not self._matches:
            return

        count = len(self._matches)

        if count > 1000:
            content = self._get_content()
            query = self.query
            replacement = self.replacement
            case_sensitive = self.case_sensitive

            self._status_label.setText("Replacing…")
            self._replace_all_btn.setEnabled(False)
            self._find_next_btn.setEnabled(False)
            self._find_prev_btn.setEnabled(False)
            self._replace_btn.setEnabled(False)

            self._cancel_bg_search()
            gen = self._search_generation
            self._replace_gen = gen

            self._bg_done.clear()
            self._bg_result = None

            def _worker():
                result = FindReplaceEngine.replace_all(
                    content, query, replacement, case_sensitive
                )
                if self._search_generation == gen:
                    self._bg_result = result
                self._bg_done.set()

            self._bg_thread = threading.Thread(target=_worker, daemon=True)
            self._bg_thread.start()

            self._replace_poll_timer = QTimer(self)
            self._replace_poll_timer.setInterval(self._POLL_MS)
            self._replace_poll_timer.timeout.connect(
                lambda: self._poll_replace_all(gen)
            )
            self._replace_poll_timer.start()
        else:
            cursor = self._editor.textCursor()
            cursor.beginEditBlock()
            for start, end in reversed(self._matches):
                cursor.setPosition(start)
                cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
                cursor.insertText(self.replacement)
            cursor.endEditBlock()
            self._status_label.setText(f"Replaced {count} occurrence(s)")
            self._start_bg_search()

    def _ensure_replace_complete(self):
        """Block until any pending background replace-all finishes (for tests)."""
        if self._bg_thread is not None and self._replace_poll_timer is not None:
            self._bg_done.wait()
            self._poll_replace_all(self._replace_gen)
        # Also drain any incremental content load timer
        if hasattr(self, '_rc_timer') and self._rc_timer is not None:
            while self._rc_timer is not None:
                self._rc_step()

    def _poll_replace_all(self, gen: int):
        """Check if the background replace-all has finished."""
        if not self._bg_done.is_set():
            return
        self._replace_poll_timer.stop()
        self._replace_poll_timer.deleteLater()
        self._replace_poll_timer = None
        self._bg_thread = None

        result = self._bg_result
        self._bg_result = None

        self._replace_all_btn.setEnabled(True)
        self._find_next_btn.setEnabled(True)
        self._find_prev_btn.setEnabled(True)
        self._replace_btn.setEnabled(True)

        if result is None or self._search_generation != gen:
            self._status_label.setText("Replace cancelled")
            return

        new_content, replaced = result
        if replaced > 0:
            self._apply_replaced_content(new_content)
        self._status_label.setText(f"Replaced {replaced} occurrence(s)")
        self._start_bg_search()

    _REPLACE_LOAD_CHUNK = 128_000
    _REPLACE_BUDGET_MS = 8

    def _apply_replaced_content(self, new_content: str):
        """Load *new_content* into the editor incrementally to avoid stalls."""
        from PySide6.QtCore import QElapsedTimer as _QET

        doc = self._editor.document()
        doc.blockSignals(True)
        self._editor.blockSignals(True)
        self._editor.setUpdatesEnabled(False)
        self._editor.setReadOnly(True)
        doc.setUndoRedoEnabled(False)

        doc.clear()
        cursor = QTextCursor(doc)
        cursor.movePosition(QTextCursor.MoveOperation.End)

        self._rc_text = new_content
        self._rc_offset = 0
        self._rc_cursor = cursor

        self._rc_timer = QTimer(self)
        self._rc_timer.setInterval(0)
        self._rc_timer.timeout.connect(self._rc_step)
        self._rc_timer.start()

    def _rc_step(self):
        """Insert replacement content in time-budgeted chunks."""
        from PySide6.QtCore import QElapsedTimer as _QET
        elapsed = _QET()
        elapsed.start()
        total = len(self._rc_text)
        chunk = self._REPLACE_LOAD_CHUNK

        while self._rc_offset < total and elapsed.elapsed() < self._REPLACE_BUDGET_MS:
            end = min(self._rc_offset + chunk, total)
            self._rc_cursor.insertText(self._rc_text[self._rc_offset:end])
            self._rc_offset = end

        if self._rc_offset >= total:
            self._rc_timer.stop()
            self._rc_timer.deleteLater()
            self._rc_timer = None
            doc = self._editor.document()
            doc.setUndoRedoEnabled(True)
            self._editor.setUpdatesEnabled(True)
            self._editor.setReadOnly(False)
            self._editor.blockSignals(False)
            doc.blockSignals(False)
            self._rc_text = None
            self._rc_cursor = None
    
    def _on_viewport_scrolled(self, rect, dy):
        """Coalesce highlight refresh when viewport scrolls."""
        if dy != 0 and self._matches and len(self._matches) > self._HIGHLIGHT_ALL_THRESHOLD:
            if not self._scroll_highlight_timer.isActive():
                self._scroll_highlight_timer.start()
    
    def closeEvent(self, event):
        """Clear highlights when closing."""
        self._cancel_bg_search()
        self._clear_highlights()
        super().closeEvent(event)
    
    def hideEvent(self, event):
        """Clear highlights when hiding."""
        self._cancel_bg_search()
        self._clear_highlights()
        super().hideEvent(event)


class MultiFileFindDialog(QDialog):
    """
    Dialog for finding and replacing across all open documents.
    """
    
    goto_match_requested = Signal(object, int)  # document, position
    
    _POLL_MS = 30

    def __init__(self, get_documents_func, get_pane_func, parent=None):
        super().__init__(parent)
        self._get_documents = get_documents_func
        self._get_pane = get_pane_func
        self._results: List[DocumentMatches] = []
        
        # Background search state
        self._bg_thread: threading.Thread | None = None
        self._bg_result: List[DocumentMatches] | None = None
        self._bg_done = threading.Event()
        self._bg_done.set()
        self._search_generation: int = 0
        
        self._poll_timer = QTimer(self)
        self._poll_timer.setInterval(self._POLL_MS)
        self._poll_timer.timeout.connect(self._poll_search)
        
        self._setup_ui()
        self.setWindowTitle("Find in Open Files")
        self.setMinimumSize(600, 400)
        self.resize(700, 500)
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Find:"))
        self._find_edit = QLineEdit()
        self._find_edit.returnPressed.connect(self._do_search)
        search_layout.addWidget(self._find_edit, 1)
        
        self._case_checkbox = QCheckBox("Match Case")
        search_layout.addWidget(self._case_checkbox)
        
        self._search_btn = QPushButton("Search")
        self._search_btn.clicked.connect(self._do_search)
        search_layout.addWidget(self._search_btn)
        
        layout.addLayout(search_layout)
        
        replace_group = QGroupBox("Replace")
        replace_layout = QVBoxLayout(replace_group)
        
        replace_input_layout = QHBoxLayout()
        replace_input_layout.addWidget(QLabel("Replace with:"))
        self._replace_edit = QLineEdit()
        replace_input_layout.addWidget(self._replace_edit, 1)
        replace_layout.addLayout(replace_input_layout)
        
        replace_btn_layout = QHBoxLayout()
        replace_btn_layout.addStretch()
        self._replace_all_btn = QPushButton("Replace All in Open Files")
        self._replace_all_btn.clicked.connect(self._do_replace_all)
        self._replace_all_btn.setEnabled(False)
        replace_btn_layout.addWidget(self._replace_all_btn)
        replace_layout.addLayout(replace_btn_layout)
        
        layout.addWidget(replace_group)
        
        self._status_label = QLabel("Enter search text and click Search")
        layout.addWidget(self._status_label)
        
        self._result_tree = QTreeWidget()
        self._result_tree.setHeaderLabels(["File / Match", "Line", "Preview"])
        self._result_tree.setColumnWidth(0, 200)
        self._result_tree.setColumnWidth(1, 50)
        self._result_tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self._result_tree, 1)
        
        close_layout = QHBoxLayout()
        close_layout.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        close_layout.addWidget(close_btn)
        layout.addLayout(close_layout)
    
    def show_find(self):
        """Show the dialog for find."""
        self._find_edit.setFocus()
        self._find_edit.selectAll()
        self.show()
    
    def show_replace(self):
        """Show the dialog for replace."""
        self._find_edit.setFocus()
        self._find_edit.selectAll()
        self.show()
    
    @property
    def query(self) -> str:
        return self._find_edit.text()
    
    @property
    def replacement(self) -> str:
        return self._replace_edit.text()
    
    @property
    def case_sensitive(self) -> bool:
        return self._case_checkbox.isChecked()
    
    def _do_search(self):
        """Perform search across all open documents in a background thread."""
        self._result_tree.clear()
        self._results = []
        self._replace_all_btn.setEnabled(False)
        
        if not self.query:
            self._status_label.setText("Enter search text")
            return
        
        # Sync editor content on the main thread before searching
        documents = self._get_documents()
        doc_contents: List[Tuple["Document", str]] = []
        for doc in documents:
            pane = self._get_pane(doc)
            if pane:
                pane.sync_from_editor()
            doc_contents.append((doc, doc.content))
        
        query = self.query
        case_sensitive = self.case_sensitive
        self._search_generation += 1
        gen = self._search_generation
        self._bg_done.clear()
        self._bg_result = None
        self._status_label.setText("Searching…")
        self._search_btn.setEnabled(False)
        
        def _worker():
            results: List[DocumentMatches] = []
            for doc, content in doc_contents:
                if self._search_generation != gen:
                    break
                matches = FindReplaceEngine.find_all(content, query, case_sensitive)
                if matches:
                    results.append(DocumentMatches(document=doc, matches=matches))
            if self._search_generation == gen:
                self._bg_result = results
            self._bg_done.set()
        
        self._bg_thread = threading.Thread(target=_worker, daemon=True)
        self._bg_thread.start()
        self._poll_timer.start()
    
    def _poll_search(self):
        """Check whether the background multi-file search has finished."""
        if not self._bg_done.is_set():
            return
        self._poll_timer.stop()
        self._search_btn.setEnabled(True)
        result = self._bg_result
        self._bg_result = None
        self._bg_thread = None
        if result is None:
            return
        self._apply_search_results(result)
    
    def _ensure_search_complete(self):
        """Block until any pending background search finishes (for tests)."""
        if self._bg_thread is not None:
            self._bg_done.wait()
            self._poll_search()
    
    def _apply_search_results(self, results: List[DocumentMatches]):
        """Populate the tree with results produced by the background thread."""
        self._results = results
        total_matches = 0
        docs_with_matches = 0
        
        for doc_matches in results:
            doc = doc_matches.document
            total_matches += doc_matches.count
            docs_with_matches += 1
            
            doc_name = doc.file_name
            doc_path = doc.file_path or ""
            doc_item = QTreeWidgetItem([doc_name, "", doc_path])
            doc_item.setData(0, Qt.ItemDataRole.UserRole, ("doc", doc, None))
            self._result_tree.addTopLevelItem(doc_item)
            
            for match in doc_matches.matches:
                preview = match.line_text.strip()
                if len(preview) > 80:
                    preview = preview[:77] + "..."
                
                match_item = QTreeWidgetItem(["", str(match.line_number), preview])
                match_item.setData(0, Qt.ItemDataRole.UserRole, ("match", doc, match))
                doc_item.addChild(match_item)
            
            doc_item.setExpanded(True)
        
        if total_matches == 0:
            self._status_label.setText("No matches found")
            self._replace_all_btn.setEnabled(False)
        else:
            self._status_label.setText(
                f"Found {total_matches} match(es) in {docs_with_matches} file(s)"
            )
            self._replace_all_btn.setEnabled(True)
    
    def _on_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle double-click on a result item."""
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data:
            return
        
        item_type, doc, match = data
        
        if item_type == "match" and match:
            self.goto_match_requested.emit(doc, match.start)
    
    def _do_replace_all(self):
        """Replace all matches across all open documents."""
        if not self._results:
            return
        
        total_docs = len(self._results)
        total_replacements = sum(r.count for r in self._results)
        
        reply = QMessageBox.question(
            self,
            "Confirm Replace All",
            f"Replace {total_replacements} occurrence(s) in {total_docs} file(s)?\n\n"
            f"This will modify the documents. You can undo changes per document.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        docs_modified = 0
        
        for doc_matches in self._results:
            doc = doc_matches.document
            pane = self._get_pane(doc)
            
            if pane and pane.current_document == doc:
                editor = pane.editor
                cursor = editor.textCursor()
                cursor.beginEditBlock()
                
                for match in reversed(doc_matches.matches):
                    cursor.setPosition(match.start)
                    cursor.setPosition(match.end, QTextCursor.MoveMode.KeepAnchor)
                    cursor.insertText(self.replacement)
                
                cursor.endEditBlock()
            else:
                new_content, count = FindReplaceEngine.replace_all(
                    doc.content, self.query, self.replacement, self.case_sensitive
                )
                if count > 0:
                    doc.content = new_content
                    doc.is_modified = True
                    if pane:
                        pane.update_tab_title(doc)
            
            docs_modified += 1
        
        self._status_label.setText(
            f"Replaced {total_replacements} occurrence(s) in {docs_modified} file(s)"
        )
        self._do_search()
