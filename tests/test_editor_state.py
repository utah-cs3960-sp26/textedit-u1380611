"""
Tests for EditorWidget state management.

These tests use pytest-qt for Qt widget testing without user interaction.
"""

import pytest
from PySide6.QtWidgets import QApplication

from editor.editor_widget import EditorWidget
from editor.document import Document
from editor.editor_pane import EditorPane


@pytest.fixture(scope="session")
def qapp():
    """Create a QApplication instance for the test session."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def editor(qapp):
    """Create a fresh EditorWidget for each test."""
    widget = EditorWidget()
    yield widget
    widget.deleteLater()


@pytest.fixture
def pane(qapp):
    """Create a fresh EditorPane for each test."""
    widget = EditorPane()
    yield widget
    widget.deleteLater()


class TestEditorInitialState:
    """Tests for initial editor state."""
    
    def test_initial_file_path_is_none(self, editor):
        """New editor has no file path."""
        assert editor.current_file_path is None
    
    def test_initial_file_name_is_untitled(self, editor):
        """New editor shows 'Untitled' as file name."""
        assert editor.file_name == "Untitled"
    
    def test_initial_content_is_empty(self, editor):
        """New editor has empty content."""
        assert editor.get_content() == ""
    
    def test_initial_is_not_modified(self, editor):
        """New editor is not marked as modified."""
        assert editor.is_modified is False
    
    def test_initial_cursor_at_start(self, editor):
        """New editor has cursor at line 1, column 1."""
        line, col = editor.get_cursor_position()
        assert line == 1
        assert col == 1


class TestEditorSetContent:
    """Tests for set_content() method."""
    
    def test_set_content_updates_text(self, editor):
        """set_content() updates the editor text."""
        editor.set_content("Hello, World!")
        assert editor.get_content() == "Hello, World!"
    
    def test_set_content_with_path_updates_file_path(self, editor):
        """set_content() with path updates current_file_path."""
        editor.set_content("Content", "/path/to/file.txt")
        assert editor.current_file_path == "/path/to/file.txt"
    
    def test_set_content_with_path_updates_file_name(self, editor):
        """set_content() with path updates file_name property."""
        editor.set_content("Content", "/path/to/myfile.txt")
        assert editor.file_name == "myfile.txt"
    
    def test_set_content_clears_modified_state(self, editor):
        """set_content() clears the modified flag."""
        editor.setPlainText("Modified content")
        editor.set_content("New content", "/path/to/file.txt")
        assert editor.is_modified is False
    
    def test_set_content_moves_cursor_to_start(self, editor):
        """set_content() positions cursor at document start."""
        editor.set_content("Line 1\nLine 2\nLine 3")
        line, col = editor.get_cursor_position()
        assert line == 1
        assert col == 1


class TestEditorNewDocument:
    """Tests for new_document() method."""
    
    def test_new_document_clears_content(self, editor):
        """new_document() clears all text."""
        editor.set_content("Some content", "/path/to/file.txt")
        editor.new_document()
        assert editor.get_content() == ""
    
    def test_new_document_clears_file_path(self, editor):
        """new_document() resets file path to None."""
        editor.set_content("Content", "/path/to/file.txt")
        editor.new_document()
        assert editor.current_file_path is None
    
    def test_new_document_shows_untitled(self, editor):
        """new_document() sets file name to 'Untitled'."""
        editor.set_content("Content", "/path/to/file.txt")
        editor.new_document()
        assert editor.file_name == "Untitled"
    
    def test_new_document_clears_modified(self, editor):
        """new_document() clears modified state."""
        editor.setPlainText("Modified")
        editor.new_document()
        assert editor.is_modified is False


class TestEditorDirtyState:
    """Tests for document dirty state tracking."""
    
    def test_inserting_text_marks_as_modified(self, editor):
        """Inserting text marks the document as modified."""
        editor.insertPlainText("Some text")
        assert editor.is_modified is True
    
    def test_mark_as_saved_clears_modified(self, editor):
        """mark_as_saved() clears the modified flag."""
        editor.insertPlainText("Content")
        editor.mark_as_saved("/path/to/saved.txt")
        assert editor.is_modified is False
    
    def test_mark_as_saved_updates_file_path(self, editor):
        """mark_as_saved() updates the current file path."""
        editor.insertPlainText("Content")
        editor.mark_as_saved("/new/path/file.txt")
        assert editor.current_file_path == "/new/path/file.txt"
    
    def test_edit_after_save_marks_modified(self, editor):
        """Editing after save marks document as modified again."""
        editor.insertPlainText("Content")
        editor.mark_as_saved("/path/file.txt")
        editor.insertPlainText("New content")
        assert editor.is_modified is True


class TestEditorStateTransitions:
    """Tests for complex state transitions."""
    
    def test_new_then_open_transition(self, editor):
        """New -> Open transition works correctly."""
        editor.new_document()
        editor.set_content("Opened content", "/path/opened.txt")
        
        assert editor.get_content() == "Opened content"
        assert editor.current_file_path == "/path/opened.txt"
        assert editor.is_modified is False
    
    def test_open_modify_save_transition(self, editor):
        """Open -> Modify -> Save transition works correctly."""
        editor.set_content("Original", "/path/file.txt")
        editor.insertPlainText("Modified")
        
        assert editor.is_modified is True
        
        editor.mark_as_saved("/path/file.txt")
        
        assert editor.is_modified is False
        assert "Modified" in editor.get_content()
    
    def test_open_modify_new_transition(self, editor):
        """Open -> Modify -> New transition clears state."""
        editor.set_content("Content", "/path/file.txt")
        editor.setPlainText("Modified")
        editor.new_document()
        
        assert editor.get_content() == ""
        assert editor.current_file_path is None
        assert editor.is_modified is False
    
    def test_save_as_changes_file_path(self, editor):
        """Save As updates file path correctly."""
        editor.set_content("Content", "/original/path.txt")
        editor.setPlainText("New content")
        editor.mark_as_saved("/new/path.txt")
        
        assert editor.current_file_path == "/new/path.txt"
        assert editor.file_name == "path.txt"
        assert editor.is_modified is False


class TestEditorCursorPosition:
    """Tests for cursor position tracking."""
    
    def test_cursor_position_after_text_input(self, editor):
        """Cursor position updates after text input."""
        editor.setPlainText("Hello")
        line, col = editor.get_cursor_position()
        assert line == 1
    
    def test_cursor_on_second_line(self, editor):
        """Cursor position is correct on second line."""
        editor.setPlainText("Line 1\nLine 2")
        cursor = editor.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        editor.setTextCursor(cursor)
        
        line, col = editor.get_cursor_position()
        assert line == 2


class TestEditorWordWrap:
    """Tests for word wrap functionality."""
    
    def test_set_word_wrap_enabled(self, editor):
        """set_word_wrap(True) enables word wrap."""
        editor.set_word_wrap(True)
        assert editor.is_word_wrap_enabled() is True
    
    def test_set_word_wrap_disabled(self, editor):
        """set_word_wrap(False) disables word wrap."""
        editor.set_word_wrap(True)
        editor.set_word_wrap(False)
        assert editor.is_word_wrap_enabled() is False


class TestEditorFilePathSetter:
    """Test the current_file_path property setter."""
    
    def test_current_file_path_setter(self, editor):
        """current_file_path setter updates internal state."""
        assert editor.current_file_path is None
        
        editor.current_file_path = "/path/to/file.txt"
        assert editor.current_file_path == "/path/to/file.txt"
        
        editor.current_file_path = "/another/path.txt"
        assert editor.current_file_path == "/another/path.txt"
        
        editor.current_file_path = None
        assert editor.current_file_path is None


class TestMemoryOptimization:
    """Tests for memory optimization — skipping HTML for plain text."""
    
    def test_plain_text_no_html_stored(self, pane):
        """Plain text document should not store html_content."""
        doc = Document(content="Hello world\nLine 2\nLine 3")
        pane.add_document(doc)
        pane._save_current_state()
        assert doc.html_content is None
    
    def test_rich_text_stores_html(self, pane):
        """Document with has_rich_formatting=True should store HTML."""
        doc = Document(content="Hello world")
        doc.has_rich_formatting = True
        pane.add_document(doc)
        pane._save_current_state()
        assert doc.html_content is not None
    
    def test_html_document_preserves_html(self, pane):
        """Document opened as HTML should continue storing HTML."""
        doc = Document(content="", file_path="test.html")
        doc.html_content = "<html><body>Hello</body></html>"
        pane.add_document(doc)
        pane._save_current_state()
        assert doc.html_content is not None
    
    def test_has_rich_formatting_default_false(self):
        """New document should have has_rich_formatting=False."""
        doc = Document()
        assert doc.has_rich_formatting is False
    
    def test_has_rich_formatting_settable(self):
        """has_rich_formatting property should be settable."""
        doc = Document()
        doc.has_rich_formatting = True
        assert doc.has_rich_formatting is True


class TestContentDirtyTracking:
    """Tests for content dirty flag optimization."""
    
    def test_content_not_copied_when_unchanged(self, pane):
        """toPlainText() should be skipped when content hasn't changed."""
        doc = Document(content="original content")
        pane.add_document(doc)
        # Manually set content to a sentinel to verify it's NOT overwritten
        doc.content = "sentinel"
        pane._save_current_state()
        # Since no text was changed, content should remain as sentinel
        assert doc.content == "sentinel"
    
    def test_content_copied_after_text_change(self, pane):
        """toPlainText() should run after user edits text."""
        doc = Document(content="original")
        pane.add_document(doc)
        pane._editor.setPlainText("modified text")
        # textChanged fires → _content_dirty = True
        pane._save_current_state()
        assert doc.content == "modified text"
    
    def test_dirty_flag_reset_on_restore(self, pane):
        """Dirty flag should be False after restoring a document."""
        doc = Document(content="test")
        pane.add_document(doc)
        assert pane._content_dirty is False


class TestLargeDocWordWrap:
    """Tests for auto word-wrap disable on large documents."""
    
    def test_large_doc_disables_word_wrap(self, pane):
        """Documents over threshold should force NoWrap."""
        from editor.line_number_editor import LineNumberedEditor
        large_content = "x" * (EditorPane._LARGE_DOC_THRESHOLD + 1)
        doc = Document(content=large_content)
        pane.add_document(doc)
        assert pane._editor.lineWrapMode() == LineNumberedEditor.LineWrapMode.NoWrap
    
    def test_small_doc_respects_wrap_preference(self, pane):
        """Small documents should use the user's word wrap preference."""
        from editor.line_number_editor import LineNumberedEditor
        pane._word_wrap_preference = True
        doc = Document(content="small text")
        pane.add_document(doc)
        assert pane._editor.lineWrapMode() == LineNumberedEditor.LineWrapMode.WidgetWidth
    
    def test_set_word_wrap_blocked_for_large_doc(self, pane):
        """set_word_wrap(True) should be ignored for large documents."""
        from editor.line_number_editor import LineNumberedEditor
        large_content = "x" * (EditorPane._LARGE_DOC_THRESHOLD + 1)
        doc = Document(content=large_content)
        pane.add_document(doc)
        pane.set_word_wrap(True)
        assert pane._editor.lineWrapMode() == LineNumberedEditor.LineWrapMode.NoWrap
        assert pane._word_wrap_preference is True
