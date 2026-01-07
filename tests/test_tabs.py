"""
Tests for tab and pane management.
"""

import pytest
from PySide6.QtWidgets import QApplication

from editor.document import Document
from editor.editor_pane import EditorPane
from editor.split_container import SplitContainer


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
        assert pane.tab_bar.tabText(0) == "file.txt*"


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
