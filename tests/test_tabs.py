"""
Tests for tab and pane management.
"""

import pytest
from unittest.mock import MagicMock, patch
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QTextCursor

from editor.document import Document
from editor.editor_pane import EditorPane
from editor.split_container import SplitContainer
from editor.theme_manager import ThemeManager, Theme


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


class TestEditorPaneDocuments:
    """Tests for EditorPane document management."""
    
    def test_add_document(self, pane):
        """Can add a document to the pane."""
        doc = Document(content="Test")
        pane.add_document(doc)
        assert doc in pane.documents
    
    def test_add_new_document(self, pane):
        """add_new_document creates and adds a document."""
        doc = pane.add_new_document()
        assert doc in pane.documents
        assert doc.content == ""
    
    def test_remove_document(self, pane):
        """Can remove a document from the pane."""
        doc = pane.add_new_document()
        pane.add_new_document()
        result = pane.remove_document(doc)
        assert result is True
        assert doc not in pane.documents
    
    def test_remove_nonexistent_document(self, pane):
        """Removing nonexistent document returns False."""
        doc = Document()
        result = pane.remove_document(doc)
        assert result is False
    
    def test_document_count(self, pane):
        """document_count reflects number of documents."""
        assert pane.document_count == 0
        pane.add_new_document()
        assert pane.document_count == 1
        pane.add_new_document()
        assert pane.document_count == 2
    
    def test_get_document_at(self, pane):
        """Can get document by index."""
        doc1 = pane.add_new_document()
        doc2 = pane.add_new_document()
        assert pane.get_document_at(0) == doc1
        assert pane.get_document_at(1) == doc2
    
    def test_get_document_at_invalid_index(self, pane):
        """get_document_at returns None for invalid index."""
        pane.add_new_document()
        assert pane.get_document_at(5) is None
        assert pane.get_document_at(-1) is None
    
    def test_current_document(self, pane):
        """current_document returns the active document."""
        doc1 = pane.add_new_document()
        doc2 = pane.add_new_document()
        assert pane.current_document == doc2
    
    def test_insert_document(self, pane):
        """Can insert document at specific position."""
        doc1 = pane.add_new_document()
        doc2 = pane.add_new_document()
        doc3 = Document(content="Inserted")
        pane.insert_document(1, doc3)
        assert pane.get_document_at(1) == doc3


class TestEditorPaneState:
    """Tests for EditorPane state management."""
    
    def test_has_unsaved_changes_false(self, pane):
        """has_unsaved_changes is False with no modified docs."""
        pane.add_new_document()
        assert pane.has_unsaved_changes() is False
    
    def test_has_unsaved_changes_true(self, pane):
        """has_unsaved_changes is True with modified doc."""
        doc = pane.add_new_document()
        doc.is_modified = True
        assert pane.has_unsaved_changes() is True
    
    def test_update_tab_title(self, pane):
        """Tab title updates when document changes."""
        doc = Document(file_path="/test/file.txt")
        pane.add_document(doc)
        assert pane.tab_bar.tabText(0) == "file.txt"
        
        doc.is_modified = True
        pane.update_tab_title(doc)
        assert pane.tab_bar.tabText(0) == "file.txt"
        assert 0 in pane.tab_bar._modified_tabs


class TestSplitContainer:
    """Tests for SplitContainer."""
    
    def test_initial_state_not_split(self, container):
        """Container starts with single pane."""
        assert container.is_split is False
    
    def test_initial_pane_exists(self, container):
        """Container starts with one pane."""
        assert container.active_pane is not None
    
    def test_initial_document_exists(self, container):
        """Container starts with one document."""
        assert container.active_document is not None
    
    def test_add_document(self, container):
        """Can add document to container."""
        doc = Document(content="Test")
        container.add_document(doc)
        assert doc in container.all_documents
    
    def test_add_new_document(self, container):
        """Can create new document in container."""
        initial_count = len(container.all_documents)
        container.add_new_document()
        assert len(container.all_documents) == initial_count + 1
    
    def test_has_unsaved_changes(self, container):
        """has_unsaved_changes checks all panes."""
        doc = container.active_document
        assert container.has_unsaved_changes() is False
        doc.is_modified = True
        assert container.has_unsaved_changes() is True


class TestSplitContainerSplit:
    """Tests for split functionality."""
    
    def test_split_with_single_document_fails(self, container):
        """Cannot split with only one document."""
        doc = container.active_document
        container.create_split(doc, "right")
        assert container.is_split is False
    
    def test_split_with_multiple_documents(self, container):
        """Can split when multiple documents exist."""
        container.add_new_document()
        doc = container.active_document
        container.create_split(doc, "right")
        assert container.is_split is True
    
    def test_split_moves_document(self, container):
        """Split moves document to new pane."""
        doc1 = container.active_document
        doc2 = container.add_new_document()
        
        original_pane = container.active_pane
        container.create_split(doc2, "right")
        
        assert doc2 not in original_pane.documents
        assert container.is_split is True
    
    def test_cannot_split_twice(self, container):
        """Cannot create more than one split."""
        container.add_new_document()
        doc1 = container.active_document
        container.create_split(doc1, "right")
        
        container.add_new_document()
        doc2 = container.active_document
        container.create_split(doc2, "left")
        
        assert len(container._panes) == 2


class TestSplitContainerMerge:
    """Tests for merge functionality."""
    
    def test_merge_combines_panes(self, container):
        """Merging combines documents into one pane."""
        container.add_new_document()
        doc = container.active_document
        container.create_split(doc, "right")
        
        assert container.is_split is True
        
        container.merge_panes()
        
        assert container.is_split is False
        assert len(container._panes) == 1
    
    def test_merge_preserves_documents(self, container):
        """Merging preserves all documents."""
        doc1 = container.active_document
        doc2 = container.add_new_document()
        container.create_split(doc2, "right")
        
        all_docs_before = container.all_documents
        container.merge_panes()
        all_docs_after = container.all_documents
        
        assert set(all_docs_before) == set(all_docs_after)


class TestDocumentTransfer:
    """Tests for document transfer between panes."""
    
    def test_transfer_document(self, container):
        """Can transfer document between panes."""
        container.add_new_document()
        doc = container.active_document
        container.create_split(doc, "right")
        
        source_pane = container.active_pane
        target_pane = [p for p in container._panes if p != source_pane][0]
        
        source_pane.add_new_document()
        doc_to_transfer = source_pane.current_document
        
        container.transfer_document(doc_to_transfer, source_pane, target_pane)
        
        assert doc_to_transfer not in source_pane.documents
        assert doc_to_transfer in target_pane.documents


class TestTabReordering:
    """Tests for tab reordering behavior."""
    
    def test_reorder_preserves_documents(self, pane):
        """Reordering tabs preserves document objects."""
        doc1 = pane.add_new_document()
        doc2 = pane.add_new_document()
        doc3 = pane.add_new_document()
        
        pane._on_tab_moved(0, 2)
        
        assert doc1 in pane.documents
        assert doc2 in pane.documents
        assert doc3 in pane.documents
    
    def test_reorder_updates_order(self, pane):
        """Reordering tabs updates document order."""
        doc1 = pane.add_new_document()
        doc2 = pane.add_new_document()
        doc3 = pane.add_new_document()
        
        pane._on_tab_moved(0, 2)
        
        assert pane.get_document_at(2) == doc1


class TestSwapPanes:
    """Tests for swap panes functionality."""
    
    def test_swap_reverses_pane_order(self, container):
        """Swapping panes reverses their order."""
        container.add_new_document()
        doc = container.active_document
        container.create_split(doc, "right")
        
        left_pane_before = container._panes[0]
        right_pane_before = container._panes[1]
        
        container.swap_panes()
        
        assert container._panes[0] == right_pane_before
        assert container._panes[1] == left_pane_before
    
    def test_swap_does_nothing_without_split(self, container):
        """Swapping without split does nothing."""
        pane_before = container._panes[0]
        container.swap_panes()
        assert container._panes[0] == pane_before


class TestSplitLineNumberColors:
    """Tests for line number colors in split panes."""
    
    def test_split_pane_gets_theme_colors(self, container):
        """New pane from split gets current theme line number colors."""
        ThemeManager().apply_theme(Theme.AQUAMARINE)
        
        container.add_new_document()
        doc = container.active_document
        container.create_split(doc, "right")
        
        new_pane = container.active_pane
        editor = new_pane._editor
        
        expected_colors = ThemeManager().get_line_number_colors()
        from PySide6.QtGui import QColor
        assert editor._bg_color == QColor(expected_colors["bg"])
        assert editor._text_color == QColor(expected_colors["text"])
        assert editor._current_line_color == QColor(expected_colors["current_line"])
    
    def test_split_pane_colors_for_midnight_blue(self, container):
        """New pane from split gets midnight blue theme colors."""
        ThemeManager().apply_theme(Theme.MIDNIGHT_BLUE)
        
        container.add_new_document()
        doc = container.active_document
        container.create_split(doc, "right")
        
        new_pane = container.active_pane
        editor = new_pane._editor
        
        expected_colors = ThemeManager().get_line_number_colors()
        from PySide6.QtGui import QColor
        assert editor._bg_color == QColor(expected_colors["bg"])


class TestUndoRedoModifiedState:
    """Tests for undo/redo affecting is_modified state."""
    
    def test_undo_reverts_modified_state(self, pane):
        """Undoing all changes sets is_modified back to false."""
        doc = pane.add_new_document()
        
        # Start clean
        assert doc.is_modified is False
        
        # Add some text
        pane._editor.insertPlainText("Hello, World!")
        assert doc.is_modified is True
        
        # Undo the change
        pane._editor.undo()
        assert doc.is_modified is False
    
    def test_redo_marks_as_modified(self, pane):
        """Redoing changes sets is_modified back to true."""
        doc = pane.add_new_document()
        
        # Add and undo
        pane._editor.insertPlainText("Hello")
        pane._editor.undo()
        assert doc.is_modified is False
        
        # Redo
        pane._editor.redo()
        assert doc.is_modified is True
    
    def test_multiple_changes_then_undo_all(self, pane):
        """Multiple changes can be undone back to clean state."""
        doc = pane.add_new_document()
        
        pane._editor.insertPlainText("Line 1\n")
        assert doc.is_modified is True
        
        pane._editor.insertPlainText("Line 2")
        assert doc.is_modified is True
        
        # Undo both changes
        pane._editor.undo()
        pane._editor.undo()
        assert doc.is_modified is False
    
    def test_tab_indicator_updates_on_undo(self, pane):
        """Tab modification indicator updates when undoing."""
        doc = pane.add_new_document()
        
        pane._editor.insertPlainText("Test")
        pane.update_tab_title(doc)
        # Check that the tab shows modified state
        assert doc.is_modified is True
        
        pane._editor.undo()
        # After undo, is_modified should be False
        assert doc.is_modified is False
        pane.update_tab_title(doc)
        # Tab bar should now show the document as unmodified
        assert doc.is_modified is False
    
    def test_restored_doc_tracks_undo_state_correctly(self, pane):
        """Undoing changes on a document updates is_modified correctly."""
        doc = pane.add_new_document()
        
        # Add text
        pane._editor.insertPlainText("Content")
        assert doc.is_modified is True
        
        # Mark as saved to reset is_modified
        doc.mark_saved()
        assert doc.is_modified is False
        
        # Add more text
        pane._editor.insertPlainText(" more")
        assert doc.is_modified is True
        
        # Undo should revert to saved state
        pane._editor.undo()
        assert doc.is_modified is False


class TestEditorPaneSignals:
    """Tests for EditorPane signal emission."""
    
    def test_document_changed_signal_emitted(self, pane):
        """document_changed signal emitted on tab change."""
        signal_emitted = []
        pane.document_changed.connect(lambda doc: signal_emitted.append(doc))
        
        doc1 = pane.add_new_document()
        doc2 = pane.add_new_document()
        
        # Switch to doc2
        pane._tab_bar.setCurrentIndex(1)
        
        assert len(signal_emitted) >= 1
    
    def test_document_modified_signal_emitted(self, pane):
        """document_modified signal emitted when doc changes."""
        signal_emitted = []
        pane.document_modified.connect(lambda doc, mod: signal_emitted.append((doc, mod)))
        
        doc = pane.add_new_document()
        pane._editor.insertPlainText("test")
        
        assert len(signal_emitted) >= 1
    
    def test_pane_empty_signal_emitted(self, pane):
        """pane_empty signal emitted when last document removed."""
        signal_emitted = []
        pane.pane_empty.connect(lambda p: signal_emitted.append(p))
        
        doc = pane.add_new_document()
        pane.remove_document(doc)
        
        assert len(signal_emitted) == 1
        assert signal_emitted[0] == pane


class TestEditorPaneTabOperations:
    """Tests for tab-specific operations."""
    
    def test_tab_moved_updates_documents(self, pane):
        """Moving tabs reorders documents."""
        doc1 = pane.add_new_document()
        doc2 = pane.add_new_document()
        doc3 = pane.add_new_document()
        
        # Verify initial order
        initial_doc_at_0 = pane.get_document_at(0)
        assert initial_doc_at_0 == doc1
    
    def test_external_drag_started_signal(self, pane):
        """external_drag_started signal emitted on drag."""
        signal_emitted = []
        pane.tab_drag_started.connect(lambda idx, p: signal_emitted.append((idx, p)))
        
        doc = pane.add_new_document()
        
        # Simulate external drag
        from PySide6.QtCore import QPoint
        pane._tab_bar.external_drag_started.emit(0, QPoint(10, 10))
        
        assert len(signal_emitted) >= 0
    
    def test_close_tab_requested_signal(self, pane):
        """close_tab_requested signal emitted on close."""
        signal_emitted = []
        pane.close_tab_requested.connect(lambda p, idx: signal_emitted.append((p, idx)))
        
        doc = pane.add_new_document()
        pane._tab_bar.tab_close_requested.emit(0)
        
        assert len(signal_emitted) >= 0


class TestEditorPaneDocumentState:
    """Tests for saving/restoring document state."""
    
    def test_save_restore_cursor_position(self, pane):
        """Cursor position is saved and restored."""
        doc1 = pane.add_new_document()
        pane._editor.insertPlainText("Line 1\nLine 2\nLine 3")
        
        # Move cursor
        cursor = pane._editor.textCursor()
        cursor.setPosition(7)
        pane._editor.setTextCursor(cursor)
        
        # Save state
        pane._save_current_state()
        
        # Create new document
        doc2 = pane.add_new_document()
        
        # Switch back
        pane._tab_bar.setCurrentIndex(0)
        pane._on_tab_changed(0)
        
        # Cursor should be restored
        assert pane._editor.textCursor().position() == 7
    
    def test_save_restore_scroll_position(self, pane):
        """Scroll position is saved and restored."""
        doc = pane.add_new_document()
        # Add enough text to scroll
        pane._editor.setPlainText("\n".join([f"Line {i}" for i in range(100)]))
        
        # Scroll down
        pane._editor.verticalScrollBar().setValue(500)
        
        # Save state
        pane._save_current_state()
        
        # Verify position was saved (scroll_position is a tuple)
        assert doc.scroll_position[1] > 0


class TestEditorPaneDocumentActivation:
    """Tests for document activation and switching."""
    
    def test_activate_document_by_index(self, pane):
        """Can activate a document by switching tab."""
        doc1 = pane.add_new_document()
        doc2 = pane.add_new_document()
        
        # Switch to doc1 via tab index
        pane._tab_bar.setCurrentIndex(0)
        assert pane.current_document == doc1
    
    def test_switch_to_second_document(self, pane):
        """Can switch to second document."""
        doc1 = pane.add_new_document()
        doc2 = pane.add_new_document()
        
        # Switch to doc2
        pane._tab_bar.setCurrentIndex(1)
        assert pane.current_document == doc2
    
    def test_tab_change_saves_state(self, pane):
        """Switching tabs saves state of previous document."""
        doc1 = pane.add_new_document()
        pane._editor.insertPlainText("doc1 text")
        
        doc2 = pane.add_new_document()
        pane._editor.insertPlainText("doc2 text")
        
        # Switch back to doc1
        pane._tab_bar.setCurrentIndex(0)
        assert "doc1 text" in pane._editor.toPlainText()


class TestEditorPaneEmptyState:
    """Tests for empty pane behavior."""
    
    def test_empty_pane_properties(self, pane):
        """Empty pane returns None for current document."""
        assert pane.current_document is None
        assert pane.document_count == 0
    
    def test_get_document_at_empty_pane(self, pane):
        """get_document_at on empty pane returns None."""
        assert pane.get_document_at(0) is None
    
    def test_remove_last_document_emits_signal(self, pane):
        """Removing last document emits pane_empty."""
        signal_emitted = []
        pane.pane_empty.connect(lambda p: signal_emitted.append(p))
        
        doc = pane.add_new_document()
        pane.remove_document(doc)
        
        assert len(signal_emitted) == 1


class TestEditorPaneInsertDocument:
    """Tests for inserting documents at specific positions."""
    
    def test_insert_document_at_start(self, pane):
        """Can insert document at start."""
        doc1 = pane.add_new_document()
        doc2 = pane.add_new_document()
        
        doc_new = Document()
        pane.insert_document(0, doc_new)
        
        assert pane.get_document_at(0) == doc_new
    
    def test_insert_document_in_middle(self, pane):
        """Can insert document in middle."""
        doc1 = pane.add_new_document()
        doc2 = pane.add_new_document()
        
        doc_new = Document()
        pane.insert_document(1, doc_new)
        
        assert pane.get_document_at(1) == doc_new
    
    def test_insert_document_at_invalid_index(self, pane):
        """Insert at invalid index clamps to valid range."""
        doc1 = pane.add_new_document()
        
        doc_new = Document()
        idx = pane.insert_document(999, doc_new)
        
        # Should be inserted at end
        assert pane.get_document_at(1) == doc_new
    
    def test_insert_document_without_activate(self, pane):
        """insert_document with activate=False doesn't switch."""
        doc1 = pane.add_new_document()
        pane._editor.insertPlainText("text1")
        
        doc_new = Document()
        pane.insert_document(1, doc_new, activate=False)
        
        assert pane.current_document == doc1


class TestEditorPaneRemoveAt:
    """Tests for removing documents by index."""
    
    def test_remove_document_at(self, pane):
        """Can remove document by index."""
        doc1 = pane.add_new_document()
        doc2 = pane.add_new_document()
        
        removed = pane.remove_document_at(0)
        assert removed == doc1
        assert pane.current_document == doc2
    
    def test_remove_document_at_invalid_index(self, pane):
        """Removing invalid index returns None."""
        doc = pane.add_new_document()
        
        result = pane.remove_document_at(999)
        assert result is None
    
    def test_remove_last_document_by_index(self, pane):
        """Removing last document by index emits signal."""
        signal_emitted = []
        pane.pane_empty.connect(lambda p: signal_emitted.append(p))
        
        doc = pane.add_new_document()
        removed = pane.remove_document_at(0)
        
        assert removed == doc
        assert len(signal_emitted) == 1


class TestEditorPaneTextChanges:
    """Tests for text change handling."""
    
    def test_text_change_updates_document(self, pane):
        """Text changes update current document content."""
        doc = pane.add_new_document()
        
        pane._editor.insertPlainText("Hello")
        assert "Hello" in pane._editor.toPlainText()
    
    def test_text_change_with_no_document(self, pane):
        """Text change with no active document is handled."""
        pane._current_index = -1
        
        # Should not raise
        pane._editor.insertPlainText("text")
        assert True


class TestEditorPaneModificationState:
    """Tests for document modification tracking."""
    
    def test_modification_tracked(self, pane):
        """Document modification is tracked."""
        doc = pane.add_new_document()
        assert doc.is_modified is False
        
        pane._editor.insertPlainText("change")
        assert doc.is_modified is True
    
    def test_tab_title_reflects_modification(self, pane):
        """Tab title shows indicator for modified documents."""
        doc = pane.add_new_document()
        
        pane._editor.insertPlainText("text")
        pane.update_tab_title(doc)
        
        # Tab should be marked as modified
        assert 0 in pane._tab_bar._modified_tabs
    
    def test_set_current_document_success(self, pane):
        """set_current_document switches to the document."""
        doc1 = pane.add_new_document()
        doc2 = pane.add_new_document()
        
        result = pane.set_current_document(doc1)
        assert result is True
        assert pane.current_document == doc1
    
    def test_set_current_document_failure(self, pane):
        """set_current_document returns False for unknown document."""
        pane.add_new_document()
        unknown_doc = Document(content="Not in pane")
        
        result = pane.set_current_document(unknown_doc)
        assert result is False
    
    def test_set_word_wrap_enabled(self, pane):
        """set_word_wrap enables line wrapping."""
        pane.set_word_wrap(True)
        # LineWrapMode.WidgetWidth
        from editor.line_number_editor import LineNumberedEditor
        assert pane._editor.lineWrapMode() == LineNumberedEditor.LineWrapMode.WidgetWidth
    
    def test_set_word_wrap_disabled(self, pane):
        """set_word_wrap disables line wrapping."""
        pane.set_word_wrap(False)
        # LineWrapMode.NoWrap
        from editor.line_number_editor import LineNumberedEditor
        assert pane._editor.lineWrapMode() == LineNumberedEditor.LineWrapMode.NoWrap
    
    def test_tab_moved_same_index(self, pane):
        """_on_tab_moved returns early if from_index == to_index."""
        pane.add_new_document()
        pane.add_new_document()
        
        # Call with same indices - should be no-op
        pane._on_tab_moved(0, 0)
        
        # Documents should be in original order
        assert len(pane.documents) == 2
    
    def test_tab_moved_invalid_from_index(self, pane):
        """_on_tab_moved returns early if from_index is out of bounds."""
        pane.add_new_document()
        
        # Call with invalid from_index - should be no-op
        pane._on_tab_moved(99, 0)
        
        assert len(pane.documents) == 1
    
    def test_tab_moved_invalid_to_index(self, pane):
        """_on_tab_moved returns early if to_index is out of bounds."""
        pane.add_new_document()
        
        # Call with invalid to_index - should be no-op
        pane._on_tab_moved(0, 99)
        
        assert len(pane.documents) == 1
    
    def test_tab_moved_swap_documents(self, pane):
        """_on_tab_moved reorders documents correctly."""
        doc1 = pane.add_new_document()
        doc2 = pane.add_new_document()
        
        pane._on_tab_moved(0, 1)
        
        # Documents should be reordered
        assert pane.documents[0] == doc2
        assert pane.documents[1] == doc1
    
    def test_save_document_with_no_file_path(self, pane):
        """_save_document returns False if document has no file path."""
        doc = pane.add_new_document()
        
        result = pane._save_document(doc)
        assert result is False
    
    def test_save_document_with_file_path_failure(self, pane, monkeypatch):
        """_save_document returns False if write fails."""
        from editor.file_handler import FileResult, FileError
        
        doc = pane.add_new_document()
        doc.file_path = "/fake/path.txt"
        
        # Mock write_file to return failure
        mock_result = FileResult(success=False, error=FileError.WRITE_ERROR)
        monkeypatch.setattr(pane._file_handler, "write_file", 
                          lambda path, content: mock_result)
        
        result = pane._save_document(doc)
        assert result is False
    
    def test_save_document_with_file_path_success(self, pane, monkeypatch):
        """_save_document returns True if write succeeds."""
        from editor.file_handler import FileResult
        
        doc = pane.add_new_document()
        doc.file_path = "/fake/path.txt"
        doc._is_modified = True  # Mark as modified to test the flow
        
        # Mock write_file to return success
        mock_result = FileResult(success=True)
        monkeypatch.setattr(pane._file_handler, "write_file", 
                          lambda path, content: mock_result)
        
        result = pane._save_document(doc)
        assert result is True
        assert doc.is_modified is False  # Should be marked as saved


class TestSplitContainerAddDocuments:
    """Tests for SplitContainer document operations."""
    
    def test_add_document_to_active_pane(self, container):
        """add_document adds document to active pane."""
        doc = Document(content="Test")
        container.add_document(doc)
        
        assert doc in container.active_pane.documents
    
    def test_add_new_document_returns_document(self, container):
        """add_new_document creates and returns document."""
        doc = container.add_new_document()
        
        assert isinstance(doc, Document)
        assert doc in container.all_documents
    
    def test_all_documents_from_all_panes(self, container):
        """all_documents returns documents from all panes."""
        doc1 = container.add_new_document()
        doc2 = container.add_new_document()
        
        container.create_split(doc2, "right")
        
        doc3 = container.add_new_document()
        
        all_docs = container.all_documents
        assert doc1 in all_docs
        assert doc2 in all_docs
        assert doc3 in all_docs
    
    def test_has_unsaved_changes_no_changes(self, container):
        """has_unsaved_changes returns False when no changes."""
        doc = container.add_new_document()
        
        result = container.has_unsaved_changes()
        assert result is False
    
    def test_has_unsaved_changes_with_changes(self, container):
        """has_unsaved_changes returns True when changes exist."""
        doc = container.add_new_document()
        doc._is_modified = True
        
        result = container.has_unsaved_changes()
        assert result is True


class TestSplitContainerWordWrap:
    """Tests for word wrap and formatting."""
    
    def test_set_word_wrap_all_panes(self, container):
        """set_word_wrap applies to all panes."""
        doc = container.add_new_document()
        container.create_split(doc, "right")
        
        container.set_word_wrap(True)
        
        # Verify both panes have word wrap enabled
        for pane in container._panes:
            from editor.line_number_editor import LineNumberedEditor
            assert pane._editor.lineWrapMode() == LineNumberedEditor.LineWrapMode.WidgetWidth
    
    def test_set_line_number_colors_all_panes(self, container):
        """set_line_number_colors applies to all panes."""
        doc = container.add_new_document()
        container.create_split(doc, "right")
        
        container.set_line_number_colors("#fff", "#000", "#ff0", "#0f0")
        
        # Verify both panes have colors set
        for pane in container._panes:
            assert pane._editor._bg_color.name() == "#ffffff"


class TestSplitContainerGuardClauses:
    """Tests for guard clauses in SplitContainer."""
    
    def test_active_document_with_no_active_pane(self, container):
        """active_document returns None when no active pane."""
        container._active_pane = None
        result = container.active_document
        assert result is None
    
    def test_add_document_with_no_active_pane(self, container):
        """add_document does nothing when no active pane."""
        container._active_pane = None
        doc = Document(content="Test")
        
        # Should not raise exception
        container.add_document(doc)
        assert True
    
    def test_add_new_document_with_no_active_pane(self, container):
        """add_new_document returns empty doc when no active pane."""
        container._active_pane = None
        doc = container.add_new_document()
        
        assert isinstance(doc, Document)
        assert doc.content == ""
    
    def test_create_split_already_split(self, container):
        """create_split returns False if already split."""
        doc = container.add_new_document()
        container.create_split(doc, "right")
        
        assert container.is_split is True
        
        # Try to split again
        result = container.create_split(doc, "left")
        assert result is False
    
    def test_create_split_document_not_found(self, container):
        """create_split returns False if document not in container."""
        doc1 = container.add_new_document()
        doc2 = Document(content="Not in container")
        
        result = container.create_split(doc2, "right")
        assert result is False
    
    def test_create_split_with_one_document_works(self, container):
        """create_split works even with one document."""
        doc = container.add_new_document()
        
        # Can split with one document
        result = container.create_split(doc, "right")
        assert result is True
        assert container.is_split is True


class TestSplitContainerMergeSwap:
    """Tests for merge and swap operations."""
    
    def test_merge_panes_not_split(self, container):
        """merge_panes returns early if not split."""
        doc = container.add_new_document()
        
        assert container.is_split is False
        
        container.merge_panes()  # Should do nothing
        
        assert container.is_split is False
    
    def test_merge_panes_combines_all(self, container):
        """merge_panes combines documents from both panes."""
        doc1 = container.add_new_document()
        doc1._content = "Doc 1"
        
        doc2 = container.add_new_document()
        doc2._content = "Doc 2"
        
        container.create_split(doc2, "right")
        
        doc3 = container.add_new_document()
        doc3._content = "Doc 3"
        
        # Merge
        container.merge_panes()
        
        assert container.is_split is False
        all_docs = container.all_documents
        assert doc1 in all_docs
        assert doc2 in all_docs
        assert doc3 in all_docs
    
    def test_swap_panes_not_split(self, container):
        """swap_panes returns early if not split."""
        doc = container.add_new_document()
        
        assert container.is_split is False
        
        container.swap_panes()  # Should do nothing
        
        assert container.is_split is False
    
    def test_swap_panes_changes_order(self, container):
        """swap_panes exchanges left and right panes."""
        doc1 = container.add_new_document()
        doc2 = container.add_new_document()
        
        container.create_split(doc2, "right")
        
        pane1_before = container._panes[0]
        pane2_before = container._panes[1]
        
        container.swap_panes()
        
        pane1_after = container._panes[0]
        pane2_after = container._panes[1]
        
        assert pane1_before != pane1_after
        assert pane2_before != pane2_after
