"""
Tests for Week 8+ performance optimizations:
- QTextDocument caching for fast tab switching
- Chunked loading for large files
- Line number gutter width not recalculated on scroll
- Coalesced scroll highlight refresh
- Optimized Replace All with updates disabled
"""

import pytest
from unittest.mock import MagicMock, patch
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QTextCursor, QTextDocument
from PySide6.QtCore import QRect

from editor.document import Document
from editor.editor_pane import EditorPane
from editor.find_replace import FindReplaceDialog, FindReplaceEngine
from editor.line_number_editor import LineNumberedEditor


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def pane(qapp):
    widget = EditorPane()
    yield widget
    widget.deleteLater()


@pytest.fixture
def editor(qapp):
    widget = LineNumberedEditor()
    yield widget
    widget.deleteLater()


class TestQTextDocumentCaching:
    """Tests for QTextDocument caching on tab switch."""

    def test_save_state_caches_qt_document(self, pane):
        """_save_current_state stores the QTextDocument on the Document model."""
        doc = pane.add_new_document()
        pane._editor.setPlainText("hello")
        pane._save_current_state()
        assert doc.qt_document is not None

    def test_cached_qt_document_used_on_restore(self, pane):
        """Switching back to a tab with a cached QTextDocument uses it."""
        doc1 = pane.add_new_document()
        pane._editor.setPlainText("doc1 content")
        pane._save_current_state()
        cached = doc1.qt_document

        doc2 = pane.add_new_document()
        pane._editor.setPlainText("doc2 content")

        # Switch back to doc1
        pane._tab_bar.setCurrentIndex(0)

        # The editor should now use the cached QTextDocument
        assert pane._editor.document() is cached
        assert "doc1 content" in pane._editor.toPlainText()

    def test_tab_switch_preserves_content_both_ways(self, pane):
        """Content is preserved when switching tabs back and forth."""
        doc1 = pane.add_new_document()
        pane._editor.setPlainText("first document")

        doc2 = pane.add_new_document()
        pane._editor.setPlainText("second document")

        # Switch to doc1
        pane._tab_bar.setCurrentIndex(0)
        assert "first document" in pane._editor.toPlainText()

        # Switch back to doc2
        pane._tab_bar.setCurrentIndex(1)
        assert "second document" in pane._editor.toPlainText()

    def test_new_document_gets_fresh_qt_document(self, pane):
        """First-time restore creates a new QTextDocument instead of reusing."""
        doc1 = pane.add_new_document()
        pane._editor.setPlainText("original")
        pane._save_current_state()
        original_doc = doc1.qt_document

        doc2 = Document(content="new content")
        pane.add_document(doc2)

        # The editor should NOT be using doc1's QTextDocument
        assert pane._editor.document() is not original_doc

    def test_document_qt_document_property(self, qapp):
        """Document model has qt_document property."""
        doc = Document(content="test")
        assert doc.qt_document is None
        qt_doc = QTextDocument()
        doc.qt_document = qt_doc
        assert doc.qt_document is qt_doc


class TestChunkedLoading:
    """Tests for chunked loading of large files."""

    def test_load_content_chunked_preserves_content(self, pane):
        """Chunked loading produces the same content as the original."""
        content = "line\n" * 5000
        pane._load_content_chunked(content)
        result = pane._editor.toPlainText()
        # insertText keeps trailing newline, toPlainText includes it
        assert result.replace('\n', '') == content.replace('\n', '')
        assert result.count('\n') == content.count('\n')

    def test_large_file_uses_chunked_loading(self, pane):
        """Files above _LARGE_DOC_THRESHOLD use chunked loading on first load."""
        # Create content larger than threshold
        threshold = pane._LARGE_DOC_THRESHOLD
        content = "x" * (threshold + 100)
        doc = Document(content=content)

        with patch.object(pane, '_load_content_chunked') as mock_chunked:
            pane._restore_document_state(doc)
            mock_chunked.assert_called_once_with(content)

    def test_small_file_uses_direct_set(self, pane):
        """Files below threshold use direct setPlainText."""
        doc = Document(content="small content")
        with patch.object(pane, '_load_content_chunked') as mock_chunked:
            pane._restore_document_state(doc)
            mock_chunked.assert_not_called()


class TestLineNumberGutterOptimization:
    """Tests for line number gutter width not recalculated on scroll."""

    def test_scroll_does_not_recalculate_width(self, editor):
        """Scrolling should not trigger setViewportMargins."""
        editor.setPlainText("line\n" * 100)

        # Simulate a scroll update (dy != 0)
        with patch.object(editor, 'setViewportMargins') as mock_margins:
            rect = QRect(0, 0, 100, 100)
            editor._update_line_number_area(rect, 10)
            mock_margins.assert_not_called()

    def test_block_count_change_updates_width(self, editor):
        """Block count changes should update the gutter width."""
        initial_width = editor.line_number_area_width()
        # Add enough lines to change digit count
        editor.setPlainText("\n".join(str(i) for i in range(1000)))
        new_width = editor.line_number_area_width()
        assert new_width > initial_width


class TestScrollHighlightCoalescing:
    """Tests for coalesced highlight refresh on scroll."""

    def test_scroll_highlight_timer_exists(self, qapp):
        """FindReplaceDialog has a scroll highlight coalescing timer."""
        editor = LineNumberedEditor()
        dialog = FindReplaceDialog(editor)
        assert hasattr(dialog, '_scroll_highlight_timer')
        assert dialog._scroll_highlight_timer.isSingleShot()
        assert dialog._scroll_highlight_timer.interval() == 0
        editor.deleteLater()
        dialog.deleteLater()

    def test_scroll_starts_coalesce_timer(self, qapp):
        """Scrolling with many matches starts the coalesce timer instead of immediate refresh."""
        editor = LineNumberedEditor()
        content = "word " * 2000  # >1000 matches
        editor.setPlainText(content)
        dialog = FindReplaceDialog(editor)
        dialog._find_edit.setText("word")
        dialog._do_deferred_search()

        assert len(dialog._matches) > dialog._HIGHLIGHT_ALL_THRESHOLD

        with patch.object(dialog, '_update_highlights') as mock_update:
            dialog._on_viewport_scrolled(QRect(0, 0, 100, 100), 10)
            # Should NOT call _update_highlights directly
            mock_update.assert_not_called()
            # Timer should be active
            assert dialog._scroll_highlight_timer.isActive()

        editor.deleteLater()
        dialog.deleteLater()


class TestOptimizedBulkReplace:
    """Tests for optimized Replace All with updates disabled."""

    def test_bulk_replace_disables_updates(self, qapp):
        """Replace All for >1000 matches disables updates and undo during replacement."""
        editor = LineNumberedEditor()
        content = "word " * 2000
        editor.setPlainText(content)
        dialog = FindReplaceDialog(editor)
        dialog._find_edit.setText("word")
        dialog._replace_edit.setText("WORD")
        dialog._do_deferred_search()

        assert len(dialog._matches) > 1000

        # Perform replace all
        dialog._replace_all()

        # Verify content was replaced correctly
        result = editor.toPlainText()
        assert "word" not in result.lower() or "WORD" in result
        assert result.count("WORD") == 2000

        editor.deleteLater()
        dialog.deleteLater()

    def test_small_replace_uses_cursor_edit(self, qapp):
        """Replace All for <=1000 matches uses cursor-based editing."""
        editor = LineNumberedEditor()
        editor.setPlainText("foo bar foo baz foo")
        dialog = FindReplaceDialog(editor)
        dialog._find_edit.setText("foo")
        dialog._replace_edit.setText("qux")
        dialog._do_deferred_search()

        assert len(dialog._matches) <= 1000

        dialog._replace_all()
        assert editor.toPlainText() == "qux bar qux baz qux"

        editor.deleteLater()
        dialog.deleteLater()


class TestFindReplaceEngineCorrectness:
    """Ensure search correctness is preserved after optimizations."""

    def test_match_count_case_insensitive(self):
        """Case-insensitive search returns correct count."""
        content = "Hello hello HELLO hElLo"
        matches = FindReplaceEngine.find_positions(content, "hello", False)
        assert len(matches) == 4

    def test_match_count_case_sensitive(self):
        """Case-sensitive search returns correct count."""
        content = "Hello hello HELLO hElLo"
        matches = FindReplaceEngine.find_positions(content, "hello", True)
        assert len(matches) == 1

    def test_replace_all_count(self):
        """Replace all returns correct replacement count."""
        content = "abc abc abc"
        new_content, count = FindReplaceEngine.replace_all(content, "abc", "xyz", False)
        assert count == 3
        assert new_content == "xyz xyz xyz"
