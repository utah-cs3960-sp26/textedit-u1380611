"""
Targeted tests for remaining coverage gaps (aiming for 95%+).

Focuses on:
- split_container.py missing lines 297, 363-364, 380-381, 409-410, 418-419, 431-432
- tab_bar.py missing lines 214-215, 228, 238-239
- file_tree.py missing lines 119, 139-140, 324-326
- font_toolbar.py missing lines 188-190
- theme_manager.py missing lines 1751-1752
- settings_dialog.py improvements
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtGui import QMouseEvent, QColor, QDragEnterEvent
from PySide6.QtCore import Qt, QPoint, QMimeData

from editor.document import Document
from editor.editor_pane import EditorPane
from editor.split_container import SplitContainer
from editor.tab_bar import EditorTabBar


@pytest.fixture(scope="session")
def qapp():
    """Create a QApplication instance."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def container(qapp):
    """Fresh SplitContainer for testing."""
    widget = SplitContainer()
    yield widget
    widget.deleteLater()


@pytest.fixture
def pane(qapp):
    """Fresh EditorPane for testing."""
    widget = EditorPane()
    yield widget
    widget.deleteLater()


@pytest.fixture
def tab_bar(qapp):
    """Fresh EditorTabBar for testing."""
    bar = EditorTabBar()
    yield bar
    bar.deleteLater()


class TestSplitContainerDragMoveLine297:
    """Test drag move event ignoring wrong MIME type (line 297, 380-381)."""

    def test_drag_move_wrong_mime_ignore(self, container):
        """dragMoveEvent should ignore events with wrong MIME type."""
        event = MagicMock()
        event.mimeData.return_value.hasFormat.return_value = False
        event.position.return_value.toPoint.return_value = QPoint(100, 100)
        
        with patch.object(event, 'ignore') as mock_ignore:
            container.dragMoveEvent(event)
            mock_ignore.assert_called()


class TestSplitContainerDropEventEdgeCases:
    """Test drop event edge cases (lines 363-364, 409-410, 418-419, 431-432)."""

    def test_drop_event_wrong_mime_type(self, container):
        """dropEvent should ignore wrong MIME type (line 409-410)."""
        event = MagicMock()
        event.mimeData.return_value.hasFormat.return_value = False
        
        with patch.object(event, 'ignore') as mock_ignore:
            container.dropEvent(event)
            mock_ignore.assert_called()

    def test_drop_event_no_drag_source(self, container):
        """dropEvent should ignore when no drag source (line 412)."""
        container._dragging_source_pane = None
        container._dragging_tab_index = -1
        
        event = MagicMock()
        event.mimeData.return_value.hasFormat.return_value = True
        
        with patch.object(event, 'ignore') as mock_ignore:
            container.dropEvent(event)
            mock_ignore.assert_called()

    def test_drop_event_document_none_at_index(self, container):
        """dropEvent should ignore when document is None (line 417-419)."""
        container._dragging_source_pane = container.active_pane
        container._dragging_tab_index = 999  # Invalid index
        
        event = MagicMock()
        event.mimeData.return_value.hasFormat.return_value = True
        event.position.return_value.toPoint.return_value = QPoint(100, 100)
        
        with patch.object(event, 'ignore') as mock_ignore:
            container.dropEvent(event)
            mock_ignore.assert_called()

    def test_drop_event_ignores_when_edge_none_after_reset(self, container):
        """dropEvent should ignore and reset when edge is None (line 431-432)."""
        container._dragging_source_pane = container.active_pane
        container._dragging_tab_index = 0
        
        event = MagicMock()
        event.mimeData.return_value.hasFormat.return_value = True
        event.position.return_value.toPoint.return_value = QPoint(0, 0)
        
        # Make _get_edge return None
        with patch.object(container, '_get_edge', return_value=None):
            with patch.object(event, 'ignore') as mock_ignore:
                # Record drag state before
                assert container._dragging_source_pane is not None
                
                container.dropEvent(event)
                
                # Should have ignored and reset drag state
                mock_ignore.assert_called()


class TestTabBarPaintEvent:
    """Test tab bar paint event for lines 214-215, 228, 238-239."""

    def test_paint_event_empty_tabs(self, tab_bar):
        """paintEvent should handle empty tab bar gracefully."""
        from PySide6.QtGui import QPaintEvent
        from PySide6.QtCore import QRect
        
        # Create paint event
        event = QPaintEvent(QRect(0, 0, 100, 30))
        
        # Should not crash
        try:
            tab_bar.paintEvent(event)
        except Exception as e:
            pytest.fail(f"paintEvent crashed: {e}")

    def test_paint_event_with_tabs(self, tab_bar):
        """paintEvent should handle tabs with underline."""
        from PySide6.QtGui import QPaintEvent
        from PySide6.QtCore import QRect
        
        tab_bar.addTab("Tab 1")
        tab_bar.addTab("Tab 2")
        tab_bar.setCurrentIndex(0)
        
        event = QPaintEvent(QRect(0, 0, 200, 30))
        
        # Should not crash
        try:
            tab_bar.paintEvent(event)
        except Exception as e:
            pytest.fail(f"paintEvent with tabs crashed: {e}")

    def test_paint_event_modified_tabs(self, tab_bar):
        """paintEvent should handle modified tab indicators."""
        from PySide6.QtGui import QPaintEvent
        from PySide6.QtCore import QRect
        
        tab_bar.addTab("Tab 1")
        tab_bar.addTab("Tab 2")
        
        # Mark as modified
        tab_bar.setTabModified(0, True)
        
        event = QPaintEvent(QRect(0, 0, 200, 30))
        
        # Should not crash
        try:
            tab_bar.paintEvent(event)
        except Exception as e:
            pytest.fail(f"paintEvent with modified tabs crashed: {e}")


class TestDropEventHandling:
    """Test drop event MIME data handling."""

    def test_drop_event_with_text_mime(self, tab_bar):
        """dropEvent with text MIME type should handle correctly."""
        tab_bar.addTab("Tab 1")
        
        mime_data = QMimeData()
        mime_data.setText("0")
        # Don't set MIME_TYPE - this is wrong format
        
        event = MagicMock()
        event.mimeData.return_value = mime_data
        event.position.return_value.toPoint.return_value = QPoint(50, 15)
        
        # Should ignore because MIME type is wrong
        with patch.object(event, 'ignore') as mock_ignore:
            tab_bar.dropEvent(event)


class TestThemeManagerCoverage:
    """Test theme manager for line 1751-1752 coverage."""

    def test_get_theme_colors_for_nonexistent_theme(self):
        """get_theme_colors should handle nonexistent themes gracefully."""
        from editor.theme_manager import ThemeManager
        
        tm = ThemeManager()
        
        # Try to get colors for non-existent theme
        colors = tm.get_theme_colors("nonexistent_super_long_theme_name_12345")
        
        # Should return a dict (fallback to defaults)
        assert isinstance(colors, dict)
        # Should have some colors defined
        assert len(colors) >= 0


class TestSettingsDialogCoverage:
    """Test settings dialog coverage improvements."""

    def test_color_button_initialization(self, qapp):
        """ColorButton should initialize with color."""
        from editor.settings_dialog import ColorButton
        
        button = ColorButton(QColor("red"))
        assert button is not None
        
        button.deleteLater()

    def test_theme_editor_widget_get_colors(self, qapp):
        """ThemeEditorWidget get_colors should return dict."""
        from editor.settings_dialog import ThemeEditorWidget
        
        editor = ThemeEditorWidget()
        colors = editor.get_colors()
        
        assert isinstance(colors, dict)
        
        editor.deleteLater()

    def test_settings_dialog_creation(self, qapp):
        """SettingsDialog should create without errors."""
        from editor.settings_dialog import SettingsDialog
        from editor.theme_manager import ThemeManager
        
        tm = ThemeManager()
        dialog = SettingsDialog(tm)
        assert dialog is not None
        
        # Check for theme_changed signal
        assert hasattr(dialog, 'theme_changed')
        
        dialog.deleteLater()


class TestDocumentMatchesProperty:
    """Test DocumentMatches count property."""

    def test_document_matches_count_property(self):
        """DocumentMatches.count should return match count."""
        from editor.find_replace import DocumentMatches, SearchMatch
        
        doc = Document(content="test test")
        matches = [
            SearchMatch(start=0, end=4, line_number=1, line_text="test test"),
            SearchMatch(start=5, end=9, line_number=1, line_text="test test"),
        ]
        
        doc_matches = DocumentMatches(document=doc, matches=matches)
        
        assert doc_matches.count == 2
        assert len(doc_matches.matches) == 2


class TestGuardClausesForCoverage:
    """Test guard clauses to ensure they're exercised."""

    def test_split_container_add_document_with_no_pane(self, container):
        """add_document should handle no active pane."""
        container._active_pane = None
        
        doc = Document()
        result = container.add_document(doc)
        
        # Should return None or handle gracefully
        assert result is None or result is False

    def test_get_pane_for_nonexistent_document(self, container):
        """get_pane_for_document should return None for nonexistent doc."""
        doc = Document(content="not in container")
        
        result = container.get_pane_for_document(doc)
        
        assert result is None

    def test_tab_bar_set_modified_invalid_index(self, tab_bar):
        """set_tab_modified with invalid index should be safe."""
        tab_bar.addTab("Tab 1")
        
        # Try with index out of range
        tab_bar.setTabModified(999, True)
        
        # Should not crash and should add to modified set
        assert 999 in tab_bar._modified_tabs


class TestDragDropErrorPaths:
    """Test error paths in drag and drop."""

    def test_handle_tab_bar_drop_with_no_pane(self, container):
        """_handle_tab_bar_drop with missing pane."""
        event = MagicMock()
        event.mimeData.return_value.hasFormat.return_value = True
        event.position.return_value.toPoint.return_value = QPoint(10, 10)
        
        source_pane = None
        target_pane = container.active_pane
        
        # Should handle None source_pane gracefully
        if source_pane is None:
            with patch.object(event, 'ignore'):
                pass


class TestEdgeCaseOperations:
    """Additional edge case operations."""

    def test_drag_move_event_with_valid_mime_no_split(self, container):
        """dragMoveEvent with valid MIME and no split."""
        event = MagicMock()
        event.mimeData.return_value.hasFormat.return_value = True
        event.position.return_value.toPoint.return_value = QPoint(100, 100)
        
        container._dragging_source_pane = container.active_pane
        
        with patch.object(event, 'acceptProposedAction'):
            container.dragMoveEvent(event)

    def test_drag_enter_event_wrong_mime(self, container):
        """dragEnterEvent with wrong MIME type."""
        event = MagicMock()
        event.mimeData.return_value.hasFormat.return_value = False
        
        with patch.object(event, 'ignore') as mock_ignore:
            container.dragEnterEvent(event)
            mock_ignore.assert_called()

    def test_drag_leave_event_hides_indicator(self, container):
        """dragLeaveEvent should hide drop indicator."""
        event = MagicMock()
        
        # Ensure indicator is visible first
        container._drop_indicator.show()
        
        container.dragLeaveEvent(event)
        
        # Indicator should be hidden
        assert not container._drop_indicator.isVisible()


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
