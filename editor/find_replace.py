"""
Find and Replace Module

Provides find/replace functionality for single documents and across open tabs.
"""

import bisect
import re
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
    def find_positions(content: str, query: str, case_sensitive: bool = False) -> List[Tuple[int, int]]:
        """Fast search returning only (start, end) position tuples. No line info."""
        if not query:
            return []
        
        if case_sensitive:
            positions = []
            pos = 0
            qlen = len(query)
            while True:
                idx = content.find(query, pos)
                if idx == -1:
                    break
                positions.append((idx, idx + qlen))
                pos = idx + 1
            return positions
        else:
            # Use re.finditer with IGNORECASE to avoid content.lower() copy
            # which doubles memory usage for large files
            pattern = re.compile(re.escape(query), re.IGNORECASE)
            return [(m.start(), m.end()) for m in pattern.finditer(content)]
    
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
    """
    
    _SEARCH_DEBOUNCE_MS = 300

    def __init__(self, editor: QPlainTextEdit, parent=None):
        super().__init__(parent)
        self._editor = editor
        self._matches: List[Tuple[int, int]] = []
        self._match_starts: List[int] = []  # cached for bisect lookups
        self._current_match_index: int = -1
        self._highlight_format = QTextCharFormat()
        self._highlight_format.setBackground(QBrush(QColor(255, 255, 0, 80)))
        self._current_format = QTextCharFormat()
        self._current_format.setBackground(QBrush(QColor(255, 165, 0, 150)))
        self._extra_selections = []
        
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(self._SEARCH_DEBOUNCE_MS)
        self._search_timer.timeout.connect(self._do_deferred_search)
        
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
            self._matches = []
            self._match_starts = []
            self._current_match_index = -1
            self._status_label.setText("Enter search text")
            self._clear_highlights()
            return
        self._status_label.setText("Searching...")
        self._search_timer.start()
    
    def _do_deferred_search(self):
        """Run the actual search after the debounce delay."""
        self._search_timer.stop()
        self._search()
        self._update_highlights()
    
    def _ensure_search_complete(self):
        """If a debounced search is pending, run it immediately."""
        if self._search_timer.isActive():
            self._search_timer.stop()
            self._do_deferred_search()
    
    def _search(self):
        """Perform the search and populate matches."""
        content = self._editor.toPlainText()
        self._matches = FindReplaceEngine.find_positions(content, self.query, self.case_sensitive)
        self._match_starts = [m[0] for m in self._matches]
        
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
    
    def _update_status(self):
        """Update the status label."""
        if self._matches:
            self._status_label.setText(
                f"Match {self._current_match_index + 1} of {len(self._matches)}"
            )
    
    _HIGHLIGHT_ALL_THRESHOLD = 1000

    def _update_highlights(self):
        """Update highlighting — only visible matches for large result sets."""
        self._clear_highlights()
        
        if not self._matches:
            return
        
        matches_to_highlight = self._matches
        
        if len(self._matches) > self._HIGHLIGHT_ALL_THRESHOLD:
            visible_start, visible_end = self._get_visible_range()
            if visible_start is not None:
                lo = bisect.bisect_left(self._match_starts, visible_start)
                hi = bisect.bisect_right(self._match_starts, visible_end)
                lo = max(0, lo - 2)
                hi = min(len(self._matches), hi + 2)
                matches_to_highlight = self._matches[lo:hi]
        
        selections = []
        for start, end in matches_to_highlight:
            cursor = self._editor.textCursor()
            cursor.setPosition(start)
            cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
            
            selection = QTextEdit.ExtraSelection()
            selection.cursor = cursor
            if (self._current_match_index >= 0 and
                self._current_match_index < len(self._matches) and
                self._matches[self._current_match_index] == (start, end)):
                selection.format = self._current_format
            else:
                selection.format = self._highlight_format
            selections.append(selection)
        
        self._extra_selections = selections
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
                self._search()
                self._update_highlights()
                if self._matches:
                    self._goto_current_match()
                return
        
        self._goto_current_match()
    
    def _replace_all(self):
        """Replace all matches."""
        self._ensure_search_complete()
        if not self._matches:
            return
        
        count = len(self._matches)
        
        if count > 1000:
            content = self._editor.toPlainText()
            new_content, replaced = FindReplaceEngine.replace_all(
                content, self.query, self.replacement, self.case_sensitive
            )
            if replaced > 0:
                self._editor.setPlainText(new_content)
            self._search()
            self._update_highlights()
            self._status_label.setText(f"Replaced {replaced} occurrence(s)")
        else:
            cursor = self._editor.textCursor()
            cursor.beginEditBlock()
            for start, end in reversed(self._matches):
                cursor.setPosition(start)
                cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
                cursor.insertText(self.replacement)
            cursor.endEditBlock()
            self._search()
            self._update_highlights()
            self._status_label.setText(f"Replaced {count} occurrence(s)")
    
    def _on_viewport_scrolled(self, rect, dy):
        """Refresh visible highlights when viewport scrolls."""
        if dy != 0 and self._matches and len(self._matches) > self._HIGHLIGHT_ALL_THRESHOLD:
            self._update_highlights()
    
    def closeEvent(self, event):
        """Clear highlights when closing."""
        self._clear_highlights()
        super().closeEvent(event)
    
    def hideEvent(self, event):
        """Clear highlights when hiding."""
        self._clear_highlights()
        super().hideEvent(event)


class MultiFileFindDialog(QDialog):
    """
    Dialog for finding and replacing across all open documents.
    """
    
    goto_match_requested = Signal(object, int)  # document, position
    
    def __init__(self, get_documents_func, get_pane_func, parent=None):
        super().__init__(parent)
        self._get_documents = get_documents_func
        self._get_pane = get_pane_func
        self._results: List[DocumentMatches] = []
        
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
        """Perform search across all open documents."""
        self._result_tree.clear()
        self._results = []
        
        if not self.query:
            self._status_label.setText("Enter search text")
            self._replace_all_btn.setEnabled(False)
            return
        
        documents = self._get_documents()
        total_matches = 0
        docs_with_matches = 0
        
        for doc in documents:
            pane = self._get_pane(doc)
            if pane:
                pane.sync_from_editor()
            
            content = doc.content
            matches = FindReplaceEngine.find_all(content, self.query, self.case_sensitive)
            
            if matches:
                doc_matches = DocumentMatches(document=doc, matches=matches)
                self._results.append(doc_matches)
                total_matches += len(matches)
                docs_with_matches += 1
                
                doc_name = doc.file_name
                doc_path = doc.file_path or ""
                doc_item = QTreeWidgetItem([doc_name, "", doc_path])
                doc_item.setData(0, Qt.ItemDataRole.UserRole, ("doc", doc, None))
                self._result_tree.addTopLevelItem(doc_item)
                
                for match in matches:
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
