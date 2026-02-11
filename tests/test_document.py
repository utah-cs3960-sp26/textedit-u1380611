"""
Tests for the Document model.
"""

import pytest
from editor.document import Document, CursorPosition


class TestDocumentCreation:
    """Tests for Document initialization."""
    
    def test_new_document_has_empty_content(self):
        """New document has empty content."""
        doc = Document()
        assert doc.content == ""
    
    def test_new_document_has_no_file_path(self):
        """New document has no file path."""
        doc = Document()
        assert doc.file_path is None
    
    def test_new_document_is_not_modified(self):
        """New document is not modified."""
        doc = Document()
        assert doc.is_modified is False
    
    def test_document_with_content(self):
        """Document can be created with initial content."""
        doc = Document(content="Hello, World!")
        assert doc.content == "Hello, World!"
    
    def test_document_with_file_path(self):
        """Document can be created with file path."""
        doc = Document(file_path="/path/to/file.txt")
        assert doc.file_path == "/path/to/file.txt"
    
    def test_document_has_unique_id(self):
        """Each document has a unique ID."""
        doc1 = Document()
        doc2 = Document()
        assert doc1.id != doc2.id


class TestDocumentFileName:
    """Tests for file name property."""
    
    def test_untitled_when_no_path(self):
        """file_name returns 'Untitled' when no path set."""
        doc = Document()
        assert doc.file_name == "Untitled"
    
    def test_extracts_name_from_path(self):
        """file_name extracts just the filename from path."""
        doc = Document(file_path="/path/to/myfile.txt")
        assert doc.file_name == "myfile.txt"
    
    def test_display_name_without_modification(self):
        """display_name shows filename without asterisk when not modified."""
        doc = Document(file_path="/path/file.txt")
        assert doc.display_name == "file.txt"
    
    def test_display_name_with_modification(self):
        """display_name shows filename (modification indicator is shown via blue dot in tab bar)."""
        doc = Document(file_path="/path/file.txt")
        doc.is_modified = True
        assert doc.display_name == "file.txt"


class TestDocumentModification:
    """Tests for modification state."""
    
    def test_set_modified(self):
        """Can set document as modified."""
        doc = Document()
        doc.is_modified = True
        assert doc.is_modified is True
    
    def test_mark_saved_clears_modified(self):
        """mark_saved clears the modified flag."""
        doc = Document()
        doc.is_modified = True
        doc.mark_saved()
        assert doc.is_modified is False
    
    def test_mark_saved_updates_path(self):
        """mark_saved can update the file path."""
        doc = Document()
        doc.mark_saved("/new/path/file.txt")
        assert doc.file_path == "/new/path/file.txt"
        assert doc.is_modified is False


class TestDocumentContent:
    """Tests for content management."""
    
    def test_set_content(self):
        """Can set document content."""
        doc = Document()
        doc.content = "New content"
        assert doc.content == "New content"
    
    def test_content_with_newlines(self):
        """Content preserves newlines."""
        doc = Document()
        doc.content = "Line 1\nLine 2\nLine 3"
        assert doc.content == "Line 1\nLine 2\nLine 3"
    
    def test_content_with_unicode(self):
        """Content supports unicode."""
        doc = Document()
        doc.content = "Hello 世界 🎉"
        assert doc.content == "Hello 世界 🎉"


class TestDocumentCursor:
    """Tests for cursor position."""
    
    def test_default_cursor_position(self):
        """Default cursor is at line 1, column 1."""
        doc = Document()
        assert doc.cursor_position.line == 1
        assert doc.cursor_position.column == 1
    
    def test_set_cursor_position(self):
        """Can set cursor position."""
        doc = Document()
        doc.cursor_position = CursorPosition(line=5, column=10)
        assert doc.cursor_position.line == 5
        assert doc.cursor_position.column == 10
    
    def test_cursor_with_selection(self):
        """Cursor can have selection range."""
        doc = Document()
        doc.cursor_position = CursorPosition(
            line=1, column=1,
            selection_start=0, selection_end=10
        )
        assert doc.cursor_position.selection_start == 0
        assert doc.cursor_position.selection_end == 10


class TestDocumentEquality:
    """Tests for document equality and hashing."""
    
    def test_same_document_is_equal(self):
        """Document equals itself."""
        doc = Document()
        assert doc == doc
    
    def test_different_documents_not_equal(self):
        """Different documents are not equal."""
        doc1 = Document()
        doc2 = Document()
        assert doc1 != doc2
    
    def test_document_hashable(self):
        """Documents can be used in sets."""
        doc1 = Document()
        doc2 = Document()
        doc_set = {doc1, doc2}
        assert len(doc_set) == 2
        assert doc1 in doc_set


class TestDocumentUndoHistory:
    """Tests for undo/redo history."""
    
    def test_clear_undo_history(self):
        """clear_undo_history clears both stacks."""
        doc = Document()
        doc.clear_undo_history()
        assert len(doc._undo_stack) == 0
        assert len(doc._redo_stack) == 0


class TestDocumentPropertySetters:
    """Tests for Document property setters."""
    
    def test_file_path_setter(self):
        """file_path setter updates internal state."""
        doc = Document()
        assert doc.file_path is None
        
        doc.file_path = "/path/to/file.txt"
        assert doc.file_path == "/path/to/file.txt"
        
        doc.file_path = "/another/path.txt"
        assert doc.file_path == "/another/path.txt"
    
    def test_document_equality_with_non_document(self):
        """Document __eq__ returns False when compared with non-Document."""
        doc = Document()
        assert (doc == "not a document") is False
        assert (doc == 42) is False
        assert (doc == None) is False
    
    def test_cursor_position_setter(self):
        """cursor_position setter updates state."""
        doc = Document()
        pos = CursorPosition(line=5, column=10)
        doc.cursor_position = pos
        assert doc.cursor_position == pos
    
    def test_scroll_position_setter(self):
        """scroll_position setter updates state."""
        doc = Document()
        assert doc.scroll_position == (0, 0)
        
        doc.scroll_position = (100, 200)
        assert doc.scroll_position == (100, 200)


class TestDocumentHtmlContent:
    """Tests for HTML content property."""
    
    def test_html_content_initially_none(self):
        """HTML content is None by default."""
        doc = Document()
        assert doc.html_content is None
    
    def test_set_html_content(self):
        """Can set HTML content."""
        doc = Document()
        doc.html_content = "<html><body>Test</body></html>"
        assert doc.html_content == "<html><body>Test</body></html>"
    
    def test_html_content_independent_of_plain_content(self):
        """HTML content is stored separately from plain content."""
        doc = Document(content="Plain text")
        doc.html_content = "<b>Bold</b>"
        assert doc.content == "Plain text"
        assert doc.html_content == "<b>Bold</b>"
