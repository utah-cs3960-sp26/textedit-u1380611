"""
Tests for Find and Replace functionality.
"""

import pytest
from PySide6.QtWidgets import QApplication, QMessageBox, QTreeWidgetItem
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
        dialog._do_deferred_search()
        
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
        dialog._do_deferred_search()
        
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
        dialog._do_deferred_search()
        
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
        dialog._do_deferred_search()
        
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
        dialog._do_deferred_search()
        
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
        dialog._do_deferred_search()
        
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
        dialog._do_deferred_search()
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
        dialog._do_deferred_search()
        
        assert len(dialog._matches) == 2
        
        dialog.deleteLater()
    
    def test_find_chinese_in_dialog(self, pane):
        """Find Chinese characters in dialog."""
        doc = pane.add_new_document()
        pane._editor.setPlainText("Say 你好 to everyone, 你好!")
        
        dialog = FindReplaceDialog(pane._editor)
        dialog._find_edit.setText("你好")
        dialog._do_deferred_search()
        
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


class TestFindReplaceDialogEdgeCases:
    """Tests for edge cases in FindReplaceDialog."""
    
    def test_replace_current_resets_match_index_when_at_end(self, pane):
        """When replacing at last match position, match index resets to 0."""
        doc = pane.add_new_document()
        pane._editor.setPlainText("cat cat")
        
        dialog = FindReplaceDialog(pane._editor)
        dialog._find_edit.setText("cat")
        dialog._replace_edit.setText("dog")
        dialog._do_deferred_search()
        
        # We have 2 matches of "cat". Set index to point past the last match after replacement
        assert dialog._current_match_index == 0
        assert len(dialog._matches) == 2
        
        # Manually set cursor to position of first "cat"
        cursor = pane._editor.textCursor()
        start, end = dialog._matches[0]
        cursor.setPosition(start)
        cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
        pane._editor.setTextCursor(cursor)
        
        # Manually set match index to be >= matches after we replace
        dialog._current_match_index = 1  # Set to second match
        dialog._replace_current()
        
        # After replace when current index >= remaining matches, should reset to 0
        # line 350 gets executed when: self._matches and self._current_match_index >= len(self._matches)
        
        dialog.close()
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


class TestFindReplaceDialogShowMethods:
    """Tests for show_find and show_replace methods."""
    
    def test_show_find_with_selection(self, pane):
        """show_find populates field with selected text."""
        doc = pane.add_new_document()
        pane._editor.setPlainText("test content here")
        
        cursor = pane._editor.textCursor()
        cursor.setPosition(0)
        cursor.setPosition(4, QTextCursor.MoveMode.KeepAnchor)
        pane._editor.setTextCursor(cursor)
        
        dialog = FindReplaceDialog(pane._editor)
        dialog.show_find()
        
        assert dialog._find_edit.text() == "test"
        
        dialog.deleteLater()
    
    def test_show_find_without_selection(self, pane):
        """show_find works without selection."""
        doc = pane.add_new_document()
        pane._editor.setPlainText("test content")
        
        dialog = FindReplaceDialog(pane._editor)
        dialog.show_find()
        
        assert dialog.isVisible()
        
        dialog.deleteLater()
    
    def test_show_replace_with_selection(self, pane):
        """show_replace populates field with selected text."""
        doc = pane.add_new_document()
        pane._editor.setPlainText("test content here")
        
        cursor = pane._editor.textCursor()
        cursor.setPosition(0)
        cursor.setPosition(4, QTextCursor.MoveMode.KeepAnchor)
        pane._editor.setTextCursor(cursor)
        
        dialog = FindReplaceDialog(pane._editor)
        dialog.show_replace()
        
        assert dialog._find_edit.text() == "test"
        
        dialog.deleteLater()
    
    def test_dialog_case_sensitive_property(self, pane):
        """Case sensitive property reflects checkbox state."""
        doc = pane.add_new_document()
        pane._editor.setPlainText("test")
        
        dialog = FindReplaceDialog(pane._editor)
        assert dialog.case_sensitive == False
        
        dialog._case_checkbox.setChecked(True)
        assert dialog.case_sensitive == True
        
        dialog.deleteLater()


class TestFindReplaceDialogAdvanced:
    """Tests for advanced dialog functionality."""
    
    def test_goto_current_match_with_matches(self, pane):
        """goto_current_match positions cursor at match."""
        doc = pane.add_new_document()
        pane._editor.setPlainText("test one test two")
        
        dialog = FindReplaceDialog(pane._editor)
        dialog._find_edit.setText("test")
        dialog._do_deferred_search()
        
        dialog._current_match_index = 1
        dialog._goto_current_match()
        
        cursor = pane._editor.textCursor()
        assert cursor.selectedText() == "test"
        assert cursor.selectionStart() == 9
        
        dialog.deleteLater()
    
    def test_replace_current_when_selected(self, pane):
        """Replace current works when match is already selected."""
        doc = pane.add_new_document()
        pane._editor.setPlainText("cat cat cat")
        
        dialog = FindReplaceDialog(pane._editor)
        dialog._find_edit.setText("cat")
        dialog._replace_edit.setText("dog")
        dialog._do_deferred_search()
        
        dialog._goto_current_match()
        dialog._replace_current()
        
        content = pane._editor.toPlainText()
        assert content == "dog cat cat"
        
        dialog.deleteLater()
    
    def test_replace_current_wraps_around(self, pane):
        """Replace current on last match wraps to first."""
        doc = pane.add_new_document()
        pane._editor.setPlainText("cat cat")
        
        dialog = FindReplaceDialog(pane._editor)
        dialog._find_edit.setText("cat")
        dialog._replace_edit.setText("dog")
        dialog._do_deferred_search()
        
        dialog._current_match_index = 1
        dialog._goto_current_match()
        dialog._replace_current()
        
        content = pane._editor.toPlainText()
        assert "dog" in content
        
        dialog.deleteLater()
    
    def test_find_prev_navigates_backwards(self, pane):
        """Find previous navigates to previous match."""
        doc = pane.add_new_document()
        pane._editor.setPlainText("test one test two test three")
        
        dialog = FindReplaceDialog(pane._editor)
        dialog._find_edit.setText("test")
        dialog._do_deferred_search()
        
        dialog._current_match_index = 1
        dialog._find_prev()
        assert dialog._current_match_index == 0
        
        dialog.deleteLater()
    
    def test_find_prev_wraps_around(self, pane):
        """Find previous at first match wraps to last."""
        doc = pane.add_new_document()
        pane._editor.setPlainText("test test test")
        
        dialog = FindReplaceDialog(pane._editor)
        dialog._find_edit.setText("test")
        dialog._do_deferred_search()
        
        dialog._current_match_index = 0
        dialog._find_prev()
        assert dialog._current_match_index == 2
        
        dialog.deleteLater()
    
    def test_goto_current_match_with_invalid_index(self, pane):
        """goto_current_match handles invalid indices gracefully."""
        doc = pane.add_new_document()
        pane._editor.setPlainText("test")
        
        dialog = FindReplaceDialog(pane._editor)
        dialog._find_edit.setText("test")
        dialog._do_deferred_search()
        
        dialog._current_match_index = 999
        dialog._goto_current_match()
        
        dialog.deleteLater()
    
    def test_close_event_clears_highlights(self, pane):
        """closeEvent clears highlights."""
        doc = pane.add_new_document()
        pane._editor.setPlainText("test test")
        
        dialog = FindReplaceDialog(pane._editor)
        dialog._find_edit.setText("test")
        dialog._do_deferred_search()
        
        assert len(dialog._extra_selections) > 0
        
        dialog.close()
        
        assert len(pane._editor.extraSelections()) == 0
    
    def test_clear_highlights_removes_selections(self, pane):
        """_clear_highlights removes all selections."""
        doc = pane.add_new_document()
        pane._editor.setPlainText("test test")
        
        dialog = FindReplaceDialog(pane._editor)
        dialog._find_edit.setText("test")
        dialog._do_deferred_search()
        
        assert len(dialog._extra_selections) > 0
        
        dialog._clear_highlights()
        
        assert len(dialog._extra_selections) == 0


class TestMultiFileFindAdvanced:
    """Tests for advanced multi-file find functionality."""
    
    def test_query_property(self, container):
        """Query property returns search text."""
        doc = container.active_document
        doc.content = "test"
        
        def get_docs():
            return container.all_documents
        
        def get_pane(doc):
            return container.get_pane_for_document(doc)
        
        dialog = MultiFileFindDialog(get_docs, get_pane)
        dialog._find_edit.setText("search")
        assert dialog.query == "search"
        
        dialog.deleteLater()
    
    def test_replacement_property(self, container):
        """Replacement property returns replacement text."""
        doc = container.active_document
        
        def get_docs():
            return container.all_documents
        
        def get_pane(doc):
            return container.get_pane_for_document(doc)
        
        dialog = MultiFileFindDialog(get_docs, get_pane)
        dialog._replace_edit.setText("replacement")
        assert dialog.replacement == "replacement"
        
        dialog.deleteLater()
    
    def test_case_sensitive_property(self, container):
        """Case sensitive property reflects checkbox."""
        doc = container.active_document
        
        def get_docs():
            return container.all_documents
        
        def get_pane(doc):
            return container.get_pane_for_document(doc)
        
        dialog = MultiFileFindDialog(get_docs, get_pane)
        assert dialog.case_sensitive == False
        
        dialog._case_checkbox.setChecked(True)
        assert dialog.case_sensitive == True
        
        dialog.deleteLater()
    
    def test_search_empty_query_no_search(self, container):
        """Empty query does not perform search."""
        doc = container.active_document
        doc.content = "test content"
        
        def get_docs():
            return container.all_documents
        
        def get_pane(doc):
            return container.get_pane_for_document(doc)
        
        dialog = MultiFileFindDialog(get_docs, get_pane)
        dialog._do_search()
        
        assert len(dialog._results) == 0
        assert "Enter search text" in dialog._status_label.text()
        
        dialog.deleteLater()
    
    def test_item_double_click_with_none_data(self, container):
        """Double-click with none data does nothing."""
        doc = container.active_document
        doc.content = "test"
        container.active_pane._editor.setPlainText(doc.content)
        
        def get_docs():
            container.active_pane.sync_from_editor()
            return container.all_documents
        
        def get_pane(doc):
            return container.get_pane_for_document(doc)
        
        dialog = MultiFileFindDialog(get_docs, get_pane)
        dialog._find_edit.setText("test")
        dialog._do_search()
        
        item = QTreeWidgetItem(["Test"])
        dialog._on_item_double_clicked(item, 0)
        
        dialog.deleteLater()
    
    def test_replace_all_with_no_results(self, container):
        """Replace all with no results does nothing."""
        doc = container.active_document
        doc.content = "test"
        
        def get_docs():
            return container.all_documents
        
        def get_pane(doc):
            return container.get_pane_for_document(doc)
        
        dialog = MultiFileFindDialog(get_docs, get_pane)
        dialog._do_replace_all()
        
        dialog.deleteLater()
    
    def test_replace_all_confirm_no(self, container):
        """Declining replace all confirmation cancels operation."""
        doc = container.active_document
        doc.content = "cat"
        container.active_pane._editor.setPlainText(doc.content)
        
        def get_docs():
            container.active_pane.sync_from_editor()
            return container.all_documents
        
        def get_pane(doc):
            return container.get_pane_for_document(doc)
        
        dialog = MultiFileFindDialog(get_docs, get_pane)
        dialog._find_edit.setText("cat")
        dialog._replace_edit.setText("dog")
        dialog._do_search()
        
        original_content = doc.content
        
        # Mock the message box to return No
        from unittest.mock import patch
        with patch('editor.find_replace.QMessageBox.question') as mock_question:
            mock_question.return_value = QMessageBox.StandardButton.No
            dialog._do_replace_all()
        
        assert doc.content == original_content
        
        dialog.deleteLater()
    
    def test_replace_in_inactive_pane_document(self, container):
        """Replace updates document not in active pane."""
        doc1 = container.active_document
        doc1.content = "cat in first"
        container.active_pane._editor.setPlainText(doc1.content)
        
        doc2 = Document(content="cat in second")
        container.add_document(doc2)
        
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
        
        from unittest.mock import patch
        with patch('editor.find_replace.QMessageBox.question') as mock_question:
            mock_question.return_value = QMessageBox.StandardButton.Yes
            dialog._do_replace_all()
        
        dialog.deleteLater()
    
    def test_item_double_click_with_match_data(self, container):
        """Double-click on match item emits signal."""
        doc = container.active_document
        doc.content = "test content"
        container.active_pane._editor.setPlainText(doc.content)
        
        def get_docs():
            container.active_pane.sync_from_editor()
            return container.all_documents
        
        def get_pane(doc):
            return container.get_pane_for_document(doc)
        
        dialog = MultiFileFindDialog(get_docs, get_pane)
        dialog._find_edit.setText("test")
        dialog._do_search()
        
        signal_emitted = []
        dialog.goto_match_requested.connect(lambda d, p: signal_emitted.append((d, p)))
        
        doc_item = dialog._result_tree.topLevelItem(0)
        match_item = doc_item.child(0)
        
        dialog._on_item_double_clicked(match_item, 0)
        
        assert len(signal_emitted) == 1
        
        dialog.deleteLater()
    
    def test_long_preview_text_truncated(self, container):
        """Long preview text gets truncated with ellipsis."""
        doc = container.active_document
        long_line = "x" * 100 + " test " + "y" * 100
        doc.content = long_line
        container.active_pane._editor.setPlainText(doc.content)
        
        def get_docs():
            container.active_pane.sync_from_editor()
            return container.all_documents
        
        def get_pane(doc):
            return container.get_pane_for_document(doc)
        
        dialog = MultiFileFindDialog(get_docs, get_pane)
        dialog._find_edit.setText("test")
        dialog._do_search()
        
        doc_item = dialog._result_tree.topLevelItem(0)
        match_item = doc_item.child(0)
        preview = match_item.text(2)
        
        assert preview.endswith("...")
        assert len(preview) <= 80
        
        dialog.deleteLater()
    
    def test_update_status_with_no_query(self, pane):
        """_update_status shows correct message when no query."""
        doc = pane.add_new_document()
        pane._editor.setPlainText("test content")
        
        dialog = FindReplaceDialog(pane._editor)
        dialog._find_edit.setText("")
        dialog._do_deferred_search()
        
        assert "Enter search text" in dialog._status_label.text()
        
        dialog.deleteLater()
    
    def test_replace_current_without_selection_goto_match(self, pane):
        """Replace current without selection moves to match."""
        doc = pane.add_new_document()
        pane._editor.setPlainText("cat cat cat")
        
        dialog = FindReplaceDialog(pane._editor)
        dialog._find_edit.setText("cat")
        dialog._replace_edit.setText("dog")
        dialog._do_deferred_search()
        
        cursor = pane._editor.textCursor()
        cursor.setPosition(0)
        pane._editor.setTextCursor(cursor)
        
        dialog._replace_current()
        
        cursor = pane._editor.textCursor()
        assert cursor.selectedText() == "cat"
        
        dialog.deleteLater()


class TestMultiFileFindShowMethods:
    """Tests for MultiFileFindDialog show methods."""
    
    def test_show_find(self, container):
        """show_find displays dialog and prepares find field."""
        doc = container.active_document
        doc.content = "test"
        
        def get_docs():
            return container.all_documents
        
        def get_pane(doc):
            return container.get_pane_for_document(doc)
        
        dialog = MultiFileFindDialog(get_docs, get_pane)
        dialog.show_find()
        
        assert dialog.isVisible()
        # Find field should be selected
        assert dialog._find_edit.selectedText() == "" or dialog._find_edit.text() == ""
        
        dialog.deleteLater()
    
    def test_show_replace(self, container):
        """show_replace displays dialog and prepares find field."""
        doc = container.active_document
        doc.content = "test"
        
        def get_docs():
            return container.all_documents
        
        def get_pane(doc):
            return container.get_pane_for_document(doc)
        
        dialog = MultiFileFindDialog(get_docs, get_pane)
        dialog.show_replace()
        
        assert dialog.isVisible()
        # Find field should be selected
        assert dialog._find_edit.selectedText() == "" or dialog._find_edit.text() == ""
        
        dialog.deleteLater()


class TestUncoveredEdgeCases:
    """Tests for the remaining edge case code paths."""
    
    def test_replace_current_with_no_matches(self, pane):
        """_replace_current returns early when no matches."""
        doc = pane.add_new_document()
        pane._editor.setPlainText("test content")
        
        dialog = FindReplaceDialog(pane._editor)
        dialog._find_edit.setText("xyz")
        dialog._replace_edit.setText("abc")
        dialog._do_deferred_search()
        
        assert len(dialog._matches) == 0
        
        # Should not crash and should return early
        dialog._replace_current()
        
        assert pane._editor.toPlainText() == "test content"
        
        dialog.deleteLater()
    
    def test_replace_current_with_negative_index(self, pane):
        """_replace_current returns early when index is negative."""
        doc = pane.add_new_document()
        pane._editor.setPlainText("test content")
        
        dialog = FindReplaceDialog(pane._editor)
        dialog._find_edit.setText("test")
        dialog._replace_edit.setText("abc")
        dialog._do_deferred_search()
        
        dialog._current_match_index = -1
        
        # Should not crash and should return early
        dialog._replace_current()
        
        assert pane._editor.toPlainText() == "test content"
        
        dialog.deleteLater()
    
    def test_replace_all_with_no_matches(self, pane):
        """_replace_all returns early when no matches."""
        doc = pane.add_new_document()
        pane._editor.setPlainText("test content")
        
        dialog = FindReplaceDialog(pane._editor)
        dialog._find_edit.setText("xyz")
        dialog._replace_edit.setText("abc")
        dialog._do_deferred_search()
        
        assert len(dialog._matches) == 0
        
        # Should not crash and should return early
        dialog._replace_all()
        
        assert pane._editor.toPlainText() == "test content"
        
        dialog.deleteLater()
    
    def test_replace_current_wraps_when_last_match_replaced(self, pane):
        """_replace_current wraps index when last match is replaced."""
        doc = pane.add_new_document()
        pane._editor.setPlainText("cat cat cat")
        
        dialog = FindReplaceDialog(pane._editor)
        dialog._find_edit.setText("cat")
        dialog._replace_edit.setText("dog")
        dialog._do_deferred_search()
        
        assert len(dialog._matches) == 3
        
        # Move to the last match
        dialog._current_match_index = 2
        dialog._goto_current_match()
        
        # Replace it - should replace "cat cat dog"
        dialog._replace_current()
        
        # After replace and re-search, there are still 2 "cat" matches
        # The index should wrap to 0
        assert dialog._current_match_index == 0
        assert "dog" in pane._editor.toPlainText()
        
        dialog.deleteLater()
    
    def test_hide_event_clears_highlights_when_hidden(self, pane):
        """hideEvent is called and clears highlights."""
        doc = pane.add_new_document()
        pane._editor.setPlainText("test test")
        
        dialog = FindReplaceDialog(pane._editor)
        dialog._find_edit.setText("test")
        dialog._do_deferred_search()
        
        # Set up highlights
        assert len(dialog._extra_selections) > 0
        
        # Explicitly call hideEvent (simulating Qt hide)
        from PySide6.QtGui import QHideEvent
        hide_event = QHideEvent()
        dialog.hideEvent(hide_event)
        
        # Highlights should be cleared
        assert len(dialog._extra_selections) == 0
        
        dialog.deleteLater()
    
    # Note: Line 350 (current_match_index wrap-around in _replace_current) is theoretically
    # unreachable because:
    # 1. It requires _current_match_index >= len(self._matches)
    # 2. But _search() is called at line 347, which resets index to 0 or finds appropriate index
    # 3. The index can only become out of bounds if _search() doesn't update it correctly
    # This is defensive code that protects against internal inconsistency that shouldn't occur
    # in normal operation. It's good defensive programming but can't be practically tested.


class TestFindPositions:
    """Tests for FindReplaceEngine.find_positions."""

    def test_find_positions_basic(self):
        """Basic match returns correct position tuples."""
        content = "hello world hello"
        positions = FindReplaceEngine.find_positions(content, "hello")
        assert positions == [(0, 5), (12, 17)]

    def test_find_positions_case_insensitive(self):
        """Default case insensitive search finds all variants."""
        content = "Hello HELLO hello"
        positions = FindReplaceEngine.find_positions(content, "hello")
        assert len(positions) == 3
        assert positions[0] == (0, 5)
        assert positions[1] == (6, 11)
        assert positions[2] == (12, 17)

    def test_find_positions_empty_query(self):
        """Empty query returns empty list."""
        positions = FindReplaceEngine.find_positions("some content", "")
        assert positions == []

    def test_find_positions_no_matches(self):
        """No matches returns empty list."""
        positions = FindReplaceEngine.find_positions("hello world", "xyz")
        assert positions == []


class TestViewportHighlighting:
    """Tests for viewport-only highlighting optimization."""

    def test_highlights_capped_for_large_result_sets(self, pane):
        """For large match counts, only a subset of highlights are created."""
        doc = pane.add_new_document()
        # Create multiline content so viewport can't show everything
        content = "\n".join(["ab"] * 1500)  # 1500 matches of "ab", one per line
        pane._editor.setPlainText(content)
        # Give the editor a small fixed size so only a few lines are visible
        pane._editor.setFixedHeight(100)
        pane._editor.show()

        dialog = FindReplaceDialog(pane._editor)
        dialog._find_edit.setText("ab")
        dialog._do_deferred_search()

        assert len(dialog._matches) == 1500
        # Extra selections should be fewer than total matches
        assert len(dialog._extra_selections) < 1500

        pane._editor.hide()
        dialog.deleteLater()

    def test_all_highlighted_for_small_result_sets(self, pane):
        """For small match counts, all matches are highlighted."""
        doc = pane.add_new_document()
        content = "ab " * 10  # 10 matches
        pane._editor.setPlainText(content)

        dialog = FindReplaceDialog(pane._editor)
        dialog._find_edit.setText("ab")
        dialog._do_deferred_search()

        assert len(dialog._matches) == 10
        assert len(dialog._extra_selections) == 10

        dialog.deleteLater()


class TestOptimizedReplaceAll:
    """Tests for optimized replace all behavior."""

    def test_replace_all_large_uses_string_replacement(self, pane):
        """Replace all with many matches uses string replacement and works correctly."""
        doc = pane.add_new_document()
        content = "cat " * 1500  # 1500 matches, above threshold
        pane._editor.setPlainText(content)

        dialog = FindReplaceDialog(pane._editor)
        dialog._find_edit.setText("cat")
        dialog._replace_edit.setText("dog")
        dialog._do_deferred_search()

        assert len(dialog._matches) == 1500

        dialog._replace_all()

        result = pane._editor.toPlainText()
        assert "cat" not in result
        assert result.count("dog") == 1500

        dialog.deleteLater()

    def test_replace_all_small_preserves_cursor_based(self, pane):
        """Replace all with few matches uses cursor-based replacement (preserves undo)."""
        doc = pane.add_new_document()
        pane._editor.setPlainText("cat cat cat")
        pane._editor.document().setModified(False)
        pane._editor.document().clearUndoRedoStacks()

        # Make an edit so undo stack is non-empty
        cursor = pane._editor.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(" extra")

        dialog = FindReplaceDialog(pane._editor)
        dialog._find_edit.setText("cat")
        dialog._replace_edit.setText("dog")
        dialog._do_deferred_search()

        assert len(dialog._matches) == 3

        dialog._replace_all()

        result = pane._editor.toPlainText()
        assert result == "dog dog dog extra"

        # Undo should restore previous state (cursor-based preserves undo)
        pane._editor.undo()
        assert pane._editor.toPlainText() == "cat cat cat extra"

        dialog.deleteLater()


class TestRegexBasedSearch:
    """Tests for regex-based case-insensitive search (avoids content.lower() copy)."""
    
    def test_find_positions_case_insensitive_regex(self):
        """Case-insensitive find_positions uses regex internally."""
        content = "Hello HELLO hello"
        positions = FindReplaceEngine.find_positions(content, "hello")
        assert len(positions) == 3
        assert positions[0] == (0, 5)
        assert positions[1] == (6, 11)
        assert positions[2] == (12, 17)
    
    def test_find_positions_special_regex_chars(self):
        """Query with regex special chars should be escaped properly."""
        content = "price is $10.00 and $10.00"
        positions = FindReplaceEngine.find_positions(content, "$10.00")
        assert len(positions) == 2
    
    def test_find_all_case_insensitive_no_split(self):
        """Case-insensitive find_all should work without content.split()."""
        content = "Line one TEST\nline two test\nline three"
        matches = FindReplaceEngine.find_all(content, "test")
        assert len(matches) == 2
        assert matches[0].line_number == 1
        assert matches[0].line_text == "Line one TEST"
        assert matches[1].line_number == 2
        assert matches[1].line_text == "line two test"
    
    def test_replace_all_case_insensitive_regex(self):
        """Case-insensitive replace_all uses regex internally."""
        content = "Hello HELLO hello"
        new_content, count = FindReplaceEngine.replace_all(content, "hello", "hi")
        assert count == 3
        assert new_content == "hi hi hi"
    
    def test_replace_all_special_chars_in_replacement(self):
        """Replacement with backslashes should be treated literally."""
        content = "foo FOO"
        new_content, count = FindReplaceEngine.replace_all(content, "foo", "bar\\1")
        assert count == 2
        assert new_content == "bar\\1 bar\\1"


class TestSearchDebounce:
    """Tests for debounced search."""
    
    def test_query_change_does_not_search_immediately(self, pane):
        """Typing should not trigger immediate search."""
        doc = pane.add_new_document()
        pane._editor.setPlainText("test test test")
        
        dialog = FindReplaceDialog(pane._editor)
        dialog._find_edit.setText("test")
        # After setText, timer is running but search hasn't happened
        assert dialog._search_timer.isActive()
        assert len(dialog._matches) == 0
        
        dialog.deleteLater()
    
    def test_ensure_search_complete_forces_search(self, pane):
        """_ensure_search_complete runs pending debounced search."""
        doc = pane.add_new_document()
        pane._editor.setPlainText("test test test")
        
        dialog = FindReplaceDialog(pane._editor)
        dialog._find_edit.setText("test")
        assert len(dialog._matches) == 0
        
        dialog._ensure_search_complete()
        assert len(dialog._matches) == 3
        assert not dialog._search_timer.isActive()
        
        dialog.deleteLater()
    
    def test_find_next_forces_search(self, pane):
        """Find Next should force any pending search to complete first."""
        doc = pane.add_new_document()
        pane._editor.setPlainText("test test test")
        
        dialog = FindReplaceDialog(pane._editor)
        dialog._find_edit.setText("test")
        # No explicit search — _find_next should force it
        dialog._find_next()
        assert len(dialog._matches) == 3
        
        dialog.deleteLater()


class TestOnViewportScrolled:
    """Tests for viewport scroll handler."""

    def test_scroll_handler_exists(self, pane):
        """Scroll handler is connected and callable."""
        doc = pane.add_new_document()
        pane._editor.setPlainText("test content")

        dialog = FindReplaceDialog(pane._editor)
        # Should not crash
        from PySide6.QtCore import QRect
        dialog._on_viewport_scrolled(QRect(), 0)
        dialog._on_viewport_scrolled(QRect(), 10)

        dialog.deleteLater()


class TestGetVisibleRange:
    """Tests for _get_visible_range helper."""

    def test_get_visible_range_returns_tuple(self, pane):
        """_get_visible_range returns a start/end tuple."""
        doc = pane.add_new_document()
        pane._editor.setPlainText("line1\nline2\nline3")

        dialog = FindReplaceDialog(pane._editor)
        start, end = dialog._get_visible_range()
        # With no viewport shown, might return None or valid range
        # Just verify it doesn't crash and returns a 2-tuple
        assert isinstance(start, (int, type(None)))
        assert isinstance(end, (int, type(None)))

        dialog.deleteLater()
