"""
Comprehensive tests for SplitContainer coverage including:
- Edge split creation (left/right)
- Message box interactions for unsaved changes
- Drag-and-drop operations
- Drop indicator visualization
"""

import pytest
from unittest.mock import MagicMock, patch, Mock
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt, QPoint, QMimeData
from PySide6.QtGui import QDrag, QMouseEvent
from PySide6.QtCore import QByteArray

from editor.document import Document
from editor.editor_pane import EditorPane
from editor.split_container import SplitContainer
from editor.tab_bar import EditorTabBar


@pytest.fixture(scope="session")
def qapp():
    """Create a QApplication instance for the test session."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def container(qapp):
    """Create a fresh SplitContainer for each test."""
    widget = SplitContainer()
    yield widget
    widget.deleteLater()


class TestSplitContainerEdgeDetection:
    """Tests for edge detection and split positioning."""
    
    def test_get_edge_left_half(self, container):
        """Position in left half returns 'left'."""
        container.resize(200, 100)
        # Position at x=50 is in left half (mid=100)
        edge = container._get_edge(QPoint(50, 50))
        assert edge == "left"
    
    def test_get_edge_right_half(self, container):
        """Position in right half returns 'right'."""
        container.resize(200, 100)
        # Position at x=150 is in right half (mid=100)
        edge = container._get_edge(QPoint(150, 50))
        assert edge == "right"
    
    def test_get_edge_at_midpoint(self, container):
        """Position at exact midpoint returns 'right'."""
        container.resize(200, 100)
        # Position at x=100 (midpoint)
        edge = container._get_edge(QPoint(100, 50))
        assert edge == "right"
    
    def test_split_left_creates_left_split(self, container):
        """create_split with 'left' edge inserts pane at position 0."""
        doc1 = container.add_new_document()
        doc2 = container.add_new_document()
        
        result = container.create_split(doc2, "left")
        assert result is True
        assert container.is_split
        assert container._panes[0].current_document == doc2
        assert container._panes[1].current_document == doc1
    
    def test_split_right_creates_right_split(self, container):
        """create_split with 'right' edge appends pane."""
        doc1 = container.add_new_document()
        doc2 = container.add_new_document()
        
        result = container.create_split(doc2, "right")
        assert result is True
        assert container.is_split
        assert container._panes[0].current_document == doc1
        assert container._panes[1].current_document == doc2


class TestSplitContainerTransfer:
    """Tests for transferring documents between panes."""
    
    def test_transfer_same_pane_no_op(self, container):
        """Transferring to same pane is a no-op."""
        pane = container.active_pane
        initial_count = pane.document_count
        doc = container.add_new_document()
        
        # This should be a no-op
        container.transfer_document(doc, pane, pane)
        assert doc in pane.documents
        assert pane.document_count == initial_count + 1
    
    def test_transfer_to_different_pane(self, container):
        """Can transfer document to different pane."""
        doc1 = container.add_new_document()
        doc2 = container.add_new_document()
        
        # Create split
        container.create_split(doc2, "right")
        left_pane = container._panes[0]
        right_pane = container._panes[1]
        
        # Create another doc in left pane
        doc3 = container.add_new_document()  # Added to active (right)
        left_pane.add_new_document()
        
        # Transfer doc3 to left pane at index 0
        container.transfer_document(doc3, right_pane, left_pane, 0)
        assert doc3 in left_pane.documents
        assert doc3 not in right_pane.documents
    
    def test_transfer_without_index(self, container):
        """Transferring without index appends document."""
        doc1 = container.add_new_document()
        doc2 = container.add_new_document()
        
        container.create_split(doc2, "right")
        left_pane = container._panes[0]
        right_pane = container._panes[1]
        
        doc3 = container.add_new_document()
        container.transfer_document(doc3, right_pane, left_pane)
        
        assert doc3 in left_pane.documents
        assert left_pane.current_document == doc3


class TestSplitContainerPaneRemoval:
    """Tests for pane removal when empty."""
    
    def test_pane_empty_signal_removes_pane(self, container):
        """Pane empty signal removes the pane when multiple panes exist."""
        doc1 = container.add_new_document()
        doc2 = container.add_new_document()
        
        container.create_split(doc2, "right")
        assert container.is_split
        
        right_pane = container._panes[1]
        right_pane.pane_empty.emit(right_pane)
        
        assert not container.is_split
        assert container._panes[0].current_document == doc1


class TestSplitContainerCloseTab:
    """Tests for close tab with save prompts."""
    
    def test_close_only_tab_closes_app(self, container):
        """Closing the only tab in the only pane emits close_app_requested."""
        signal_emitted = False
        
        def on_close_app():
            nonlocal signal_emitted
            signal_emitted = True
        
        container.close_app_requested.connect(on_close_app)
        pane = container.active_pane
        container._on_close_tab_requested(pane, 0)
        
        assert signal_emitted
    
    @patch('editor.split_container.QMessageBox.warning')
    def test_close_modified_tab_prompts_save(self, mock_warning, container):
        """Closing modified document prompts to save."""
        pane = container.active_pane
        doc = pane.get_document_at(0)
        doc.is_modified = True
        # Add another document so closing doesn't trigger close_app_requested
        container.add_new_document()
        
        mock_warning.return_value = QMessageBox.StandardButton.Discard
        
        container._on_close_tab_requested(pane, 0)
        
        # Should have called the warning dialog
        assert mock_warning.called
    
    @patch('editor.split_container.QMessageBox.warning')
    def test_close_modified_cancel_keeps_document(self, mock_warning, container):
        """Canceling close keeps the document."""
        pane = container.active_pane
        doc = pane.get_document_at(0)
        doc.is_modified = True
        # Add another document so closing doesn't trigger close_app_requested
        container.add_new_document()
        
        mock_warning.return_value = QMessageBox.StandardButton.Cancel
        
        container._on_close_tab_requested(pane, 0)
        
        assert doc in pane.documents
    
    @patch('editor.split_container.QMessageBox.warning')
    def test_close_modified_discard(self, mock_warning, container):
        """Discarding changes removes the document."""
        pane = container.active_pane
        doc = pane.get_document_at(0)
        doc.content = "Modified content"
        doc.is_modified = True
        # Add another document so closing doesn't trigger close_app_requested
        container.add_new_document()
        
        mock_warning.return_value = QMessageBox.StandardButton.Discard
        
        container._on_close_tab_requested(pane, 0)
        
        assert doc not in pane.documents
    
    @patch('editor.split_container.FileHandler.write_file')
    @patch('editor.split_container.QMessageBox.warning')
    def test_close_modified_save_with_path(self, mock_warning, mock_write, container):
        """Saving with existing path saves the file."""
        pane = container.active_pane
        doc = pane.get_document_at(0)
        doc.file_path = "/tmp/test.txt"
        doc.content = "Modified content"
        doc.is_modified = True
        # Add another document so closing doesn't trigger close_app_requested
        container.add_new_document()
        
        mock_warning.return_value = QMessageBox.StandardButton.Save
        mock_write.return_value = Mock(success=True)
        
        container._on_close_tab_requested(pane, 0)
        
        mock_write.assert_called_once()
        assert not doc.is_modified
    
    @patch('editor.split_container.FileHandler.write_file')
    @patch('editor.split_container.QMessageBox.warning')
    @patch('editor.split_container.QMessageBox.critical')
    def test_close_modified_save_error(self, mock_critical, mock_warning, mock_write, container):
        """Save error shows error dialog."""
        pane = container.active_pane
        doc = pane.get_document_at(0)
        doc.file_path = "/tmp/test.txt"
        doc.is_modified = True
        # Add another document so closing doesn't trigger close_app_requested
        container.add_new_document()
        
        mock_warning.return_value = QMessageBox.StandardButton.Save
        mock_write.return_value = Mock(success=False, error_message="Write failed")
        
        container._on_close_tab_requested(pane, 0)
        
        mock_critical.assert_called_once()
        assert doc in pane.documents  # Document stays because save failed
    
    @patch('editor.split_container.QMessageBox.warning')
    def test_close_modified_save_without_path(self, mock_warning, container):
        """Saving without path emits save_document_requested."""
        signal_emitted = False
        
        def on_save_requested(doc, index, pane):
            nonlocal signal_emitted
            signal_emitted = True
        
        container.save_document_requested.connect(on_save_requested)
        
        pane = container.active_pane
        doc = pane.get_document_at(0)
        doc.is_modified = True
        # Add another document so closing doesn't trigger close_app_requested
        container.add_new_document()
        # No file_path set
        
        mock_warning.return_value = QMessageBox.StandardButton.Save
        
        container._on_close_tab_requested(pane, 0)
        
        assert signal_emitted


class TestSplitContainerDragDrop:
    """Tests for drag and drop operations."""
    
    def test_tab_drag_started_sets_state(self, container):
        """Tab drag started sets tracking variables."""
        pane = container.active_pane
        doc = container.add_new_document()
        
        container._on_tab_drag_started(0, pane)
        
        assert container._dragging_tab_index == 0
        assert container._dragging_source_pane == pane
    
    def test_reset_drag_state_clears_vars(self, container):
        """Reset drag state clears tracking variables."""
        pane = container.active_pane
        container._dragging_tab_index = 5
        container._dragging_source_pane = pane
        
        container._reset_drag_state()
        
        assert container._dragging_tab_index == -1
        assert container._dragging_source_pane is None
    
    def test_drag_enter_accepts_mime_type(self, container):
        """dragEnterEvent accepts correct MIME type."""
        event = Mock()
        event.mimeData.return_value = Mock()
        event.mimeData.return_value.hasFormat.return_value = True
        
        container.dragEnterEvent(event)
        
        event.acceptProposedAction.assert_called_once()
    
    def test_drag_enter_ignores_wrong_mime(self, container):
        """dragEnterEvent ignores wrong MIME type."""
        event = Mock()
        event.mimeData.return_value = Mock()
        event.mimeData.return_value.hasFormat.return_value = False
        
        container.dragEnterEvent(event)
        
        event.ignore.assert_called_once()
    
    def test_drag_leave_hides_indicator(self, container):
        """dragLeaveEvent hides the drop indicator."""
        container._drop_indicator.show()
        event = Mock()
        
        container.dragLeaveEvent(event)
        
        assert not container._drop_indicator.isVisible()
        
        container._drop_indicator.close()
    
    def test_drag_move_shows_left_indicator(self, container):
        """dragMoveEvent shows indicator for left edge."""
        container.resize(200, 100)
        pane = container.active_pane
        doc2 = container.add_new_document()
        
        # Setup drag state - have at least 2 documents to allow split
        container._dragging_source_pane = pane
        container._dragging_tab_index = 1
        
        event = Mock()
        event.mimeData.return_value = Mock()
        event.mimeData.return_value.hasFormat.return_value = True
        event.position.return_value = Mock()
        event.position.return_value.toPoint.return_value = QPoint(50, 50)
        
        # Should show indicator when conditions are met
        container.dragMoveEvent(event)
        
        # Verify geometry was set correctly (the geometry is set even if not visible)
        geom = container._drop_indicator.geometry()
        assert geom.x() == 0
        assert geom.width() == 100
    
    def test_drag_move_shows_right_indicator(self, container):
        """dragMoveEvent shows indicator for right edge."""
        container.resize(200, 100)
        pane = container.active_pane
        doc2 = container.add_new_document()
        
        container._dragging_source_pane = pane
        container._dragging_tab_index = 1
        
        event = Mock()
        event.mimeData.return_value = Mock()
        event.mimeData.return_value.hasFormat.return_value = True
        event.position.return_value = Mock()
        event.position.return_value.toPoint.return_value = QPoint(150, 50)
        
        # Should show indicator when conditions are met
        container.dragMoveEvent(event)
        
        # Verify geometry was set correctly
        geom = container._drop_indicator.geometry()
        assert geom.x() == 100
        assert geom.width() == 100
    
    def test_drag_move_hides_indicator_when_already_split(self, container):
        """dragMoveEvent hides indicator if already split."""
        container.resize(200, 100)
        doc1 = container.add_new_document()
        doc2 = container.add_new_document()
        container.create_split(doc2, "right")
        
        event = Mock()
        event.mimeData.return_value = Mock()
        event.mimeData.return_value.hasFormat.return_value = True
        event.position.return_value = Mock()
        event.position.return_value.toPoint.return_value = QPoint(50, 50)
        
        container.dragMoveEvent(event)
        
        assert not container._drop_indicator.isVisible()
    
    def test_drop_event_creates_split_left(self, container):
        """dropEvent creates left split."""
        container.resize(200, 100)
        doc1 = container.add_new_document()
        doc2 = container.add_new_document()
        pane = container.active_pane
        
        container._dragging_source_pane = pane
        container._dragging_tab_index = 1
        
        event = Mock()
        event.mimeData.return_value = Mock()
        event.mimeData.return_value.hasFormat.return_value = True
        event.position.return_value = Mock()
        event.position.return_value.toPoint.return_value = QPoint(50, 50)
        
        container.dropEvent(event)
        
        assert container.is_split
        event.acceptProposedAction.assert_called_once()
    
    def test_drop_event_ignores_no_drag_source(self, container):
        """dropEvent ignores if no drag source."""
        event = Mock()
        event.mimeData.return_value = Mock()
        event.mimeData.return_value.hasFormat.return_value = True
        event.position.return_value = Mock()
        event.position.return_value.toPoint.return_value = QPoint(50, 50)
        
        container._dragging_source_pane = None
        
        container.dropEvent(event)
        
        event.ignore.assert_called_once()
    
    def test_handle_tab_bar_drop_transfers_document(self, container):
        """_handle_tab_bar_drop transfers document between panes."""
        doc1 = container.add_new_document()
        doc2 = container.add_new_document()
        
        container.create_split(doc2, "right")
        left_pane = container._panes[0]
        right_pane = container._panes[1]
        
        # Create event
        event = Mock()
        event.mimeData.return_value = Mock()
        event.mimeData.return_value.hasFormat.return_value = True
        
        source_bar = left_pane.tab_bar
        event.source.return_value = source_bar
        event.mimeData.return_value.data.return_value = QByteArray(b"0")
        
        left_pane.add_new_document()
        
        event.position.return_value = Mock()
        event.position.return_value.toPoint.return_value = QPoint(0, 0)
        
        right_pane.tab_bar.get_drop_index = Mock(return_value=-1)
        
        container._handle_tab_bar_drop(right_pane, event)
        
        event.acceptProposedAction.assert_called_once()
    
    def test_handle_tab_bar_drop_ignores_wrong_mime(self, container):
        """_handle_tab_bar_drop ignores wrong MIME type."""
        pane = container.active_pane
        event = Mock()
        event.mimeData.return_value = Mock()
        event.mimeData.return_value.hasFormat.return_value = False
        
        container._handle_tab_bar_drop(pane, event)
        
        event.ignore.assert_called_once()
    
    def test_handle_tab_bar_drop_ignores_non_tabbar_source(self, container):
        """_handle_tab_bar_drop ignores non-TabBar source."""
        pane = container.active_pane
        event = Mock()
        event.mimeData.return_value = Mock()
        event.mimeData.return_value.hasFormat.return_value = True
        event.source.return_value = Mock()  # Not a TabBar
        
        container._handle_tab_bar_drop(pane, event)
        
        event.ignore.assert_called_once()
    
    def test_handle_tab_bar_drop_ignores_same_pane(self, container):
        """_handle_tab_bar_drop ignores drop on same pane."""
        pane = container.active_pane
        doc = container.add_new_document()
        
        event = Mock()
        event.mimeData.return_value = Mock()
        event.mimeData.return_value.hasFormat.return_value = True
        event.source.return_value = pane.tab_bar
        
        container._handle_tab_bar_drop(pane, event)
        
        event.ignore.assert_called_once()


class TestSplitContainerIndicatorGeometry:
    """Tests for drop indicator visualization."""
    
    def test_drop_indicator_left_geometry(self, container):
        """Drop indicator correct geometry for left half."""
        container.resize(200, 100)
        doc1 = container.add_new_document()
        doc2 = container.add_new_document()
        pane = container.active_pane
        
        container._dragging_source_pane = pane
        container._dragging_tab_index = 1
        
        event = Mock()
        event.mimeData.return_value = Mock()
        event.mimeData.return_value.hasFormat.return_value = True
        event.position.return_value = Mock()
        event.position.return_value.toPoint.return_value = QPoint(50, 50)
        
        container.dragMoveEvent(event)
        
        geom = container._drop_indicator.geometry()
        assert geom.x() == 0
        assert geom.width() == 100
        assert geom.height() == 100
    
    def test_drop_indicator_right_geometry(self, container):
        """Drop indicator correct geometry for right half."""
        container.resize(200, 100)
        doc1 = container.add_new_document()
        doc2 = container.add_new_document()
        pane = container.active_pane
        
        container._dragging_source_pane = pane
        container._dragging_tab_index = 1
        
        event = Mock()
        event.mimeData.return_value = Mock()
        event.mimeData.return_value.hasFormat.return_value = True
        event.position.return_value = Mock()
        event.position.return_value.toPoint.return_value = QPoint(150, 50)
        
        container.dragMoveEvent(event)
        
        geom = container._drop_indicator.geometry()
        assert geom.x() == 100
        assert geom.width() == 100
        assert geom.height() == 100


class TestSplitContainerRemovePane:
    """Tests for pane removal logic."""
    
    def test_remove_pane_updates_active(self, container):
        """Removing active pane updates active_pane."""
        doc1 = container.add_new_document()
        doc2 = container.add_new_document()
        
        container.create_split(doc2, "right")
        right_pane = container._panes[1]
        
        container._active_pane = right_pane
        container._remove_pane(right_pane)
        
        assert container._active_pane == container._panes[0]
    
    def test_remove_pane_not_in_list_no_op(self, container):
        """Removing pane not in list is a no-op."""
        fake_pane = Mock()
        initial_count = len(container._panes)
        
        container._remove_pane(fake_pane)
        
        assert len(container._panes) == initial_count
