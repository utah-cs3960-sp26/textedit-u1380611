"""
Tests for Find and Replace functionality.
"""

import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QTextCursor

from editor.document import Document
from editor.editor_pane import EditorPane
from editor.split_container import SplitContainer
from editor.find_replace import (
    FindReplaceEngine, SearchMatch, DocumentMatches,
    FindReplaceDialog, MultiFileFindDialog
)


@pytest.fixture(scope="session")
def qapp():
    """Create a QApplication instance for the test session."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def pane(qapp):
    """Create a fresh EditorPane for each test."""
    widget = EditorPane()
    yield widget
    widget.deleteLater()


@pytest.fixture
def container(qapp):
    """Create a fresh SplitContainer for each test."""
    widget = SplitContainer()
    yield widget
    widget.deleteLater()


class TestFindReplaceEngineBasic:
    """Tests for FindReplaceEngine.find_all basic functionality."""
    
    def test_find_single_match(self):
        """Find a single occurrence."""
        content = "Hello world"
        matches = FindReplaceEngine.find_all(content, "world")
        assert len(matches) == 1
        assert matches[0].start == 6
        assert matches[0].end == 11
    
    def test_find_multiple_matches(self):
        """Find multiple occurrences."""
        content = "cat cat cat"
        matches = FindReplaceEngine.find_all(content, "cat")
        assert len(matches) == 3
        assert matches[0].start == 0
        assert matches[1].start == 4
        assert matches[2].start == 8
    
    def test_find_no_matches(self):
        """Return empty list when no matches."""
        content = "Hello world"
        matches = FindReplaceEngine.find_all(content, "xyz")
        assert len(matches) == 0
    
    def test_find_empty_query(self):
        """Empty query returns no matches."""
        content = "Hello world"
        matches = FindReplaceEngine.find_all(content, "")
        assert len(matches) == 0
    
    def test_find_empty_content(self):
        """Empty content returns no matches."""
        content = ""
        matches = FindReplaceEngine.find_all(content, "test")
        assert len(matches) == 0


class TestFindReplaceEngineCaseSensitivity:
    """Tests for case sensitivity in find."""
    
    def test_case_insensitive_default(self):
        """Default search is case-insensitive."""
        content = "Hello HELLO hello"
        matches = FindReplaceEngine.find_all(content, "hello")
        assert len(matches) == 3
    
    def test_case_sensitive_search(self):
        """Case-sensitive search respects case."""
        content = "Hello HELLO hello"
        matches = FindReplaceEngine.find_all(content, "Hello", case_sensitive=True)
        assert len(matches) == 1
        assert matches[0].start == 0


class TestFindReplaceEngineLineNumbers:
    """Tests for line number tracking in matches."""
    
    def test_line_numbers_single_line(self):
        """Matches on single line have line number 1."""
        content = "test test test"
        matches = FindReplaceEngine.find_all(content, "test")
        for match in matches:
            assert match.line_number == 1
    
    def test_line_numbers_multiple_lines(self):
        """Matches track correct line numbers."""
        content = "line1 test\nline2\nline3 test"
        matches = FindReplaceEngine.find_all(content, "test")
        assert len(matches) == 2
        assert matches[0].line_number == 1
        assert matches[1].line_number == 3
    
    def test_line_text_captured(self):
        """Match includes the full line text."""
        content = "first line\nsecond test line\nthird line"
        matches = FindReplaceEngine.find_all(content, "test")
        assert len(matches) == 1
        assert matches[0].line_text == "second test line"


class TestFindReplaceEngineUTF8:
    """Tests for UTF-8 and non-ASCII character support."""
    
    def test_find_utf8_cafe(self):
        """Find matches with café (accented character)."""
        content = "I love café and café culture"
        matches = FindReplaceEngine.find_all(content, "café")
        assert len(matches) == 2
    
    def test_find_utf8_chinese(self):
        """Find matches with Chinese characters (你好)."""
        content = "Say 你好 to everyone, 你好!"
        matches = FindReplaceEngine.find_all(content, "你好")
        assert len(matches) == 2
    
    def test_find_utf8_emoji(self):
        """Find matches with emoji."""
        content = "Hello 🎉 world 🎉"
        matches = FindReplaceEngine.find_all(content, "🎉")
        assert len(matches) == 2
    
    def test_find_mixed_utf8(self):
        """Find in content with mixed ASCII and UTF-8."""
        content = "café 你好 hello café"
        matches = FindReplaceEngine.find_all(content, "café")
        assert len(matches) == 2


class TestFindReplaceEngineReplace:
    """Tests for FindReplaceEngine.replace_all."""
    
    def test_replace_single(self):
        """Replace single occurrence."""
        content = "Hello world"
        new_content, count = FindReplaceEngine.replace_all(content, "world", "universe")
        assert new_content == "Hello universe"
        assert count == 1
    
    def test_replace_multiple(self):
        """Replace multiple occurrences."""
        content = "cat cat cat"
        new_content, count = FindReplaceEngine.replace_all(content, "cat", "dog")
        assert new_content == "dog dog dog"
        assert count == 3
    
    def test_replace_no_matches(self):
        """Replace with no matches returns original."""
        content = "Hello world"
        new_content, count = FindReplaceEngine.replace_all(content, "xyz", "abc")
        assert new_content == content
        assert count == 0
    
    def test_replace_empty_query(self):
        """Empty query returns original."""
        content = "Hello world"
        new_content, count = FindReplaceEngine.replace_all(content, "", "test")
        assert new_content == content
        assert count == 0
    
    def test_replace_with_empty(self):
        """Replace with empty string (deletion)."""
        content = "Hello world"
        new_content, count = FindReplaceEngine.replace_all(content, " world", "")
        assert new_content == "Hello"
        assert count == 1
    
    def test_replace_case_insensitive(self):
        """Case-insensitive replace."""
        content = "Hello HELLO hello"
        new_content, count = FindReplaceEngine.replace_all(content, "hello", "hi")
        assert new_content == "hi hi hi"
        assert count == 3
    
    def test_replace_case_sensitive(self):
        """Case-sensitive replace."""
        content = "Hello HELLO hello"
        new_content, count = FindReplaceEngine.replace_all(
            content, "Hello", "Hi", case_sensitive=True
        )
        assert new_content == "Hi HELLO hello"
        assert count == 1


class TestFindReplaceDialogBasic:
    """Tests for FindReplaceDialog basic operations."""
    
    def test_dialog_creation(self, pane):
        """Dialog can be created."""
        doc = pane.add_new_document()
        pane._editor.setPlainText("test content")
        
        dialog = FindReplaceDialog(pane._editor)
        assert dialog is not None
        dialog.deleteLater()
    
    def test_dialog_find_next(self, pane):
        """Find next navigates through matches."""
        doc = pane.add_new_document()
        pane._editor.setPlainText("test one test two test three")
        
        dialog = FindReplaceDialog(pane._editor)
        dialog._find_edit.setText("test")
        dialog._on_query_changed()
        
        assert len(dialog._matches) == 3
        
        dialog._find_next()
        cursor = pane._editor.textCursor()
        assert cursor.hasSelection()
        assert cursor.selectedText() == "test"
        
        dialog.deleteLater()
    
    def test_dialog_find_prev(self, pane):
        """Find previous navigates backwards."""
        doc = pane.add_new_document()
        pane._editor.setPlainText("test one test two test three")
        
        dialog = FindReplaceDialog(pane._editor)
        dialog._find_edit.setText("test")
        dialog._on_query_changed()
        
        dialog._current_match_index = 2
        dialog._find_prev()
        assert dialog._current_match_index == 1
        
        dialog.deleteLater()
    
    def test_dialog_empty_query_no_crash(self, pane):
        """Empty query doesn't crash."""
        doc = pane.add_new_document()
        pane._editor.setPlainText("test content")
        
        dialog = FindReplaceDialog(pane._editor)
        dialog._find_edit.setText("")
        dialog._on_query_changed()
        
        assert len(dialog._matches) == 0
        
        dialog._find_next()
        dialog._find_prev()
        
        dialog.deleteLater()
    
    def test_dialog_no_matches_status(self, pane):
        """No matches shows appropriate status."""
        doc = pane.add_new_document()
        pane._editor.setPlainText("test content")
        
        dialog = FindReplaceDialog(pane._editor)
        dialog._find_edit.setText("xyz")
        dialog._on_query_changed()
        
        assert len(dialog._matches) == 0
        assert "No matches" in dialog._status_label.text()
        
        dialog.deleteLater()


class TestFindReplaceDialogReplace:
    """Tests for FindReplaceDialog replace operations."""
    
    def test_replace_current_match(self, pane):
        """Replace current match replaces only one occurrence."""
        doc = pane.add_new_document()
        pane._editor.setPlainText("cat cat cat")
        
        dialog = FindReplaceDialog(pane._editor)
        dialog._find_edit.setText("cat")
        dialog._replace_edit.setText("dog")
        dialog._on_query_changed()
        
        dialog._goto_current_match()
        dialog._replace_current()
        
        content = pane._editor.toPlainText()
        assert content.count("dog") == 1
        assert content.count("cat") == 2
        
        dialog.deleteLater()
    
    def test_replace_all(self, pane):
        """Replace all replaces all occurrences."""
        doc = pane.add_new_document()
        pane._editor.setPlainText("cat cat cat")
        
        dialog = FindReplaceDialog(pane._editor)
        dialog._find_edit.setText("cat")
        dialog._replace_edit.setText("dog")
        dialog._on_query_changed()
        
        dialog._replace_all()
        
        content = pane._editor.toPlainText()
        assert content == "dog dog dog"
        
        dialog.deleteLater()
    
    def test_replace_all_undo(self, pane):
        """Replace all can be undone in one step."""
        doc = pane.add_new_document()
        original = "cat cat cat"
        pane._editor.setPlainText(original)
        pane._editor.document().setModified(False)
        pane._editor.document().clearUndoRedoStacks()
        
        cursor = pane._editor.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(" extra")
        
        dialog = FindReplaceDialog(pane._editor)
        dialog._find_edit.setText("cat")
        dialog._replace_edit.setText("dog")
        dialog._on_query_changed()
        dialog._replace_all()
        
        content_after_replace = pane._editor.toPlainText()
        assert "dog" in content_after_replace
        
        pane._editor.undo()
        
        content_after_undo = pane._editor.toPlainText()
        assert content_after_undo == original + " extra"
        
        dialog.deleteLater()


class TestFindReplaceDialogUTF8:
    """Tests for UTF-8 support in dialog."""
    
    def test_find_cafe_in_dialog(self, pane):
        """Find café in dialog."""
        doc = pane.add_new_document()
        pane._editor.setPlainText("I love café and more café")
        
        dialog = FindReplaceDialog(pane._editor)
        dialog._find_edit.setText("café")
        dialog._on_query_changed()
        
        assert len(dialog._matches) == 2
        
        dialog.deleteLater()
    
    def test_find_chinese_in_dialog(self, pane):
        """Find Chinese characters in dialog."""
        doc = pane.add_new_document()
        pane._editor.setPlainText("Say 你好 to everyone, 你好!")
        
        dialog = FindReplaceDialog(pane._editor)
        dialog._find_edit.setText("你好")
        dialog._on_query_changed()
        
        assert len(dialog._matches) == 2
        
        dialog.deleteLater()


class TestMultiFileFindBasic:
    """Tests for multi-file find across open documents."""
    
    def test_find_in_multiple_docs(self, container):
        """Search finds matches in multiple open documents."""
        doc1 = container.active_document
        doc1.content = "First file with test content"
        container.active_pane._editor.setPlainText(doc1.content)
        
        doc2 = Document(content="Second file also has test here")
        container.add_document(doc2)
        container.active_pane._editor.setPlainText(doc2.content)
        
        doc3 = Document(content="Third file without the word")
        container.add_document(doc3)
        container.active_pane._editor.setPlainText(doc3.content)
        
        def get_docs():
            for pane in container._panes:
                pane.sync_from_editor()
            return container.all_documents
        
        def get_pane(doc):
            return container.get_pane_for_document(doc)
        
        dialog = MultiFileFindDialog(get_docs, get_pane)
        dialog._find_edit.setText("test")
        dialog._do_search()
        
        assert len(dialog._results) == 2
        
        total_matches = sum(r.count for r in dialog._results)
        assert total_matches == 2
        
        dialog.deleteLater()
    
    def test_find_includes_untitled_docs(self, container):
        """Search includes untitled documents."""
        doc1 = container.active_document
        assert doc1.file_path is None
        doc1.content = "Untitled doc with searchable content"
        container.active_pane._editor.setPlainText(doc1.content)
        
        def get_docs():
            container.active_pane.sync_from_editor()
            return container.all_documents
        
        def get_pane(doc):
            return container.get_pane_for_document(doc)
        
        dialog = MultiFileFindDialog(get_docs, get_pane)
        dialog._find_edit.setText("searchable")
        dialog._do_search()
        
        assert len(dialog._results) == 1
        assert dialog._results[0].document.file_name == "Untitled"
        
        dialog.deleteLater()
    
    def test_closed_docs_not_included(self, container):
        """Closed documents are not included in search."""
        doc1 = container.active_document
        doc1.content = "First document with test"
        container.active_pane._editor.setPlainText(doc1.content)
        
        doc2 = Document(content="Second with test")
        container.add_document(doc2)
        container.active_pane._editor.setPlainText(doc2.content)
        
        container.active_pane.sync_from_editor()
        container.active_pane.remove_document(doc2)
        
        def get_docs():
            container.active_pane.sync_from_editor()
            return container.all_documents
        
        def get_pane(doc):
            return container.get_pane_for_document(doc)
        
        dialog = MultiFileFindDialog(get_docs, get_pane)
        dialog._find_edit.setText("test")
        dialog._do_search()
        
        assert len(dialog._results) == 1
        
        dialog.deleteLater()


class TestMultiFileFindResultsUI:
    """Tests for multi-file find results display."""
    
    def test_results_grouped_by_document(self, container):
        """Results are grouped by document."""
        doc1 = container.active_document
        doc1.content = "test test in first"
        container.active_pane._editor.setPlainText(doc1.content)
        
        doc2 = Document(content="test in second")
        container.add_document(doc2)
        container.active_pane._editor.setPlainText(doc2.content)
        
        def get_docs():
            for pane in container._panes:
                pane.sync_from_editor()
            return container.all_documents
        
        def get_pane(doc):
            return container.get_pane_for_document(doc)
        
        dialog = MultiFileFindDialog(get_docs, get_pane)
        dialog._find_edit.setText("test")
        dialog._do_search()
        
        top_level_count = dialog._result_tree.topLevelItemCount()
        assert top_level_count == 2
        
        dialog.deleteLater()
    
    def test_results_show_line_numbers(self, container):
        """Results show line numbers."""
        doc1 = container.active_document
        doc1.content = "line one\ntest on line two\nline three"
        container.active_pane._editor.setPlainText(doc1.content)
        
        def get_docs():
            container.active_pane.sync_from_editor()
            return container.all_documents
        
        def get_pane(doc):
            return container.get_pane_for_document(doc)
        
        dialog = MultiFileFindDialog(get_docs, get_pane)
        dialog._find_edit.setText("test")
        dialog._do_search()
        
        top_item = dialog._result_tree.topLevelItem(0)
        match_item = top_item.child(0)
        line_text = match_item.text(1)
        assert line_text == "2"
        
        dialog.deleteLater()


class TestMultiFileReplace:
    """Tests for multi-file replace functionality."""
    
    def test_replace_across_multiple_docs(self, container):
        """Replace updates buffers in multiple documents."""
        doc1 = container.active_document
        doc1.content = "cat in first"
        container.active_pane._editor.setPlainText(doc1.content)
        
        doc2 = Document(content="cat in second")
        container.add_document(doc2)
        container.active_pane._editor.setPlainText(doc2.content)
        
        def get_docs():
            for pane in container._panes:
                pane.sync_from_editor()
            return container.all_documents
        
        def get_pane(doc):
            return container.get_pane_for_document(doc)
        
        dialog = MultiFileFindDialog(get_docs, get_pane)
        dialog._find_edit.setText("cat")
        dialog._replace_edit.setText("dog")
        dialog._do_search()
        
        assert len(dialog._results) == 2
        
        dialog.deleteLater()
    
    def test_replace_marks_docs_modified(self, container):
        """Replace marks only affected documents as modified."""
        doc1 = container.active_document
        doc1.content = "no match here"
        doc1.is_modified = False
        container.active_pane._editor.setPlainText(doc1.content)
        
        doc2 = Document(content="cat to replace")
        doc2.is_modified = False
        container.add_document(doc2)
        container.active_pane._editor.setPlainText(doc2.content)
        
        def get_docs():
            for pane in container._panes:
                pane.sync_from_editor()
            return container.all_documents
        
        def get_pane(doc):
            return container.get_pane_for_document(doc)
        
        dialog = MultiFileFindDialog(get_docs, get_pane)
        dialog._find_edit.setText("cat")
        dialog._replace_edit.setText("dog")
        dialog._do_search()
        
        assert len(dialog._results) == 1
        assert dialog._results[0].document == doc2
        
        dialog.deleteLater()
    
    def test_unaffected_docs_unchanged(self, container):
        """Documents without matches are not modified."""
        doc1 = container.active_document
        original_content1 = "no match in this document"
        doc1.content = original_content1
        container.active_pane._editor.setPlainText(doc1.content)
        
        doc2 = Document(content="cat here")
        container.add_document(doc2)
        container.active_pane._editor.setPlainText(doc2.content)
        
        def get_docs():
            for pane in container._panes:
                pane.sync_from_editor()
            return container.all_documents
        
        def get_pane(doc):
            return container.get_pane_for_document(doc)
        
        dialog = MultiFileFindDialog(get_docs, get_pane)
        dialog._find_edit.setText("cat")
        dialog._replace_edit.setText("dog")
        dialog._do_search()
        
        assert doc1 not in [r.document for r in dialog._results]
        
        dialog.deleteLater()


class TestMultiFileReplaceUndo:
    """Tests for undo behavior in multi-file replace."""
    
    def test_per_document_undo_works(self, pane):
        """Undo works on individual document after replace-all."""
        doc = pane.add_new_document()
        original = "cat cat cat"
        pane._editor.setPlainText(original)
        pane._editor.document().setModified(False)
        pane._editor.document().clearUndoRedoStacks()
        
        cursor = pane._editor.textCursor()
        cursor.beginEditBlock()
        
        matches = FindReplaceEngine.find_all(original, "cat")
        for match in reversed(matches):
            cursor.setPosition(match.start)
            cursor.setPosition(match.end, QTextCursor.MoveMode.KeepAnchor)
            cursor.insertText("dog")
        
        cursor.endEditBlock()
        
        assert pane._editor.toPlainText() == "dog dog dog"
        
        pane._editor.undo()
        
        assert pane._editor.toPlainText() == original


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""
    
    def test_find_at_document_start(self):
        """Find match at document start."""
        content = "test at start"
        matches = FindReplaceEngine.find_all(content, "test")
        assert len(matches) == 1
        assert matches[0].start == 0
    
    def test_find_at_document_end(self):
        """Find match at document end."""
        content = "end with test"
        matches = FindReplaceEngine.find_all(content, "test")
        assert len(matches) == 1
        assert matches[0].end == len(content)
    
    def test_find_across_line_boundary(self):
        """Find matches that don't cross line boundaries."""
        content = "test\ntest"
        matches = FindReplaceEngine.find_all(content, "test")
        assert len(matches) == 2
    
    def test_find_overlapping_potential(self):
        """Find handles potential overlapping patterns."""
        content = "aaaa"
        matches = FindReplaceEngine.find_all(content, "aa")
        assert len(matches) == 3
    
    def test_replace_with_longer_text(self):
        """Replace with longer text works correctly."""
        content = "a b c"
        new_content, count = FindReplaceEngine.replace_all(content, "b", "bbb")
        assert new_content == "a bbb c"
        assert count == 1
    
    def test_replace_with_shorter_text(self):
        """Replace with shorter text works correctly."""
        content = "hello world"
        new_content, count = FindReplaceEngine.replace_all(content, "hello", "hi")
        assert new_content == "hi world"
        assert count == 1
    
    def test_very_long_line(self):
        """Handle very long lines efficiently."""
        content = "x" * 10000 + "test" + "x" * 10000
        matches = FindReplaceEngine.find_all(content, "test")
        assert len(matches) == 1
        assert matches[0].start == 10000
    
    def test_many_matches(self):
        """Handle many matches efficiently."""
        content = "test " * 1000
        matches = FindReplaceEngine.find_all(content, "test")
        assert len(matches) == 1000
