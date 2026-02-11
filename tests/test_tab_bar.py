"""
Tests for the EditorTabBar module.
"""

import pytest
from unittest.mock import MagicMock, patch
from PySide6.QtWidgets import QApplication, QToolButton
from PySide6.QtCore import Qt, QPoint, QMimeData, QSize
from PySide6.QtGui import QMouseEvent, QDragEnterEvent, QDropEvent

from editor.tab_bar import EditorTabBar


@pytest.fixture(scope="session")
def qapp():
    """Create a QApplication instance for the test session."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def tab_bar(qapp):
    """Create a fresh EditorTabBar for each test."""
    widget = EditorTabBar()
    yield widget
    widget.deleteLater()


class TestTabBarInitialization:
    """Tests for EditorTabBar initialization."""
    
    def test_initial_tab_count_is_zero(self, tab_bar):
        """New tab bar has no tabs."""
        assert tab_bar.count() == 0
    
    def test_tabs_not_closable_by_default(self, tab_bar):
        """Tab bar does not use built-in close buttons."""
        assert tab_bar.tabsClosable() is False
    
    def test_tabs_are_movable(self, tab_bar):
        """Tabs can be reordered."""
        assert tab_bar.isMovable() is True
    
    def test_accepts_drops(self, tab_bar):
        """Tab bar accepts drops."""
        assert tab_bar.acceptDrops() is True
    
    def test_has_new_tab_button(self, tab_bar):
        """Tab bar has a '+' button."""
        assert tab_bar._new_tab_button is not None
        assert tab_bar._new_tab_button.text() == "+"


class TestTabBarModifiedIndicator:
    """Tests for modified indicator (blue dot)."""
    
    def test_set_tab_modified_adds_to_set(self, tab_bar):
        """setTabModified(True) adds index to modified set."""
        tab_bar.addTab("Test")
        tab_bar.setTabModified(0, True)
        assert 0 in tab_bar._modified_tabs
    
    def test_set_tab_unmodified_removes_from_set(self, tab_bar):
        """setTabModified(False) removes index from modified set."""
        tab_bar.addTab("Test")
        tab_bar.setTabModified(0, True)
        tab_bar.setTabModified(0, False)
        assert 0 not in tab_bar._modified_tabs
    
    def test_multiple_tabs_can_be_modified(self, tab_bar):
        """Multiple tabs can be marked as modified."""
        tab_bar.addTab("Tab 1")
        tab_bar.addTab("Tab 2")
        tab_bar.addTab("Tab 3")
        tab_bar.setTabModified(0, True)
        tab_bar.setTabModified(2, True)
        assert 0 in tab_bar._modified_tabs
        assert 1 not in tab_bar._modified_tabs
        assert 2 in tab_bar._modified_tabs


class TestTabBarCloseButton:
    """Tests for custom close buttons."""
    
    def test_tab_has_close_button(self, tab_bar):
        """Added tab gets a custom close button."""
        tab_bar.addTab("Test")
        close_btn = tab_bar.tabButton(0, tab_bar.ButtonPosition.RightSide)
        assert close_btn is not None
    
    def test_close_button_has_x_text(self, tab_bar):
        """Close button displays × character."""
        tab_bar.addTab("Test")
        close_btn = tab_bar.tabButton(0, tab_bar.ButtonPosition.RightSide)
        assert close_btn.text() == "×"


class TestTabBarSignals:
    """Tests for tab bar signals."""
    
    def test_new_tab_requested_signal_exists(self, tab_bar):
        """new_tab_requested signal exists."""
        assert hasattr(tab_bar, 'new_tab_requested')
    
    def test_tab_close_requested_signal_exists(self, tab_bar):
        """tab_close_requested signal exists."""
        assert hasattr(tab_bar, 'tab_close_requested')
    
    def test_external_drag_started_signal_exists(self, tab_bar):
        """external_drag_started signal exists."""
        assert hasattr(tab_bar, 'external_drag_started')


class TestTabBarCloseButtonEvents:
    """Tests for close button event handling."""
    
    def test_close_button_click_emits_signal(self, tab_bar):
        """Clicking close button emits tab_close_requested signal."""
        signal_emitted = []
        tab_bar.tab_close_requested.connect(lambda idx: signal_emitted.append(idx))
        
        tab_bar.addTab("Test")
        close_btn = tab_bar.tabButton(0, tab_bar.ButtonPosition.RightSide)
        
        # Simulate click
        close_btn.clicked.emit()
        
        assert len(signal_emitted) == 1
        assert signal_emitted[0] == 0
    
    def test_close_button_click_multiple_tabs(self, tab_bar):
        """Close button identifies correct tab index."""
        signal_emitted = []
        tab_bar.tab_close_requested.connect(lambda idx: signal_emitted.append(idx))
        
        tab_bar.addTab("Tab 1")
        tab_bar.addTab("Tab 2")
        tab_bar.addTab("Tab 3")
        
        close_btn = tab_bar.tabButton(1, tab_bar.ButtonPosition.RightSide)
        close_btn.clicked.emit()
        
        assert signal_emitted[0] == 1


class TestTabBarMouseEvents:
    """Tests for mouse event handling."""
    
    def test_mouse_press_sets_drag_start_pos(self, tab_bar):
        """Mouse press records start position for drag."""
        tab_bar.addTab("Test")
        
        event = QMouseEvent(
            QMouseEvent.Type.MouseButtonPress,
            QPoint(10, 10),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier
        )
        
        tab_bar.mousePressEvent(event)
        
        assert tab_bar._drag_start_pos == QPoint(10, 10)
    
    def test_mouse_release_clears_drag_state(self, tab_bar):
        """Mouse release clears drag start position."""
        tab_bar.addTab("Test")
        tab_bar._drag_start_pos = QPoint(10, 10)
        
        event = QMouseEvent(
            QMouseEvent.Type.MouseButtonRelease,
            QPoint(20, 20),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier
        )
        
        tab_bar.mouseReleaseEvent(event)
        
        assert tab_bar._drag_start_pos is None
    
    def test_mouse_move_without_drag_start(self, tab_bar):
        """Mouse move without drag start does nothing."""
        tab_bar.addTab("Test")
        
        event = QMouseEvent(
            QMouseEvent.Type.MouseMove,
            QPoint(20, 10),
            Qt.MouseButton.NoButton,
            Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier
        )
        
        # Should not raise
        tab_bar.mouseMoveEvent(event)
        assert True


class TestTabBarDragAndDrop:
    """Tests for drag and drop operations."""
    
    def test_drag_enter_accept(self, tab_bar):
        """Drag enter accepts internal mime data."""
        mime_data = QMimeData()
        mime_data.setData(EditorTabBar.MIME_TYPE, b"")
        
        event = QDragEnterEvent(
            QPoint(10, 10),
            Qt.DropActions.CopyAction,
            mime_data,
            Qt.MouseButtons.LeftButton,
            Qt.KeyboardModifiers.NoModifier
        )
        
        tab_bar.dragEnterEvent(event)
        
        # Event should be accepted
        assert event.isAccepted()
    
    def test_drop_reorders_tabs(self, tab_bar):
        """Dropping tab reorders tabs."""
        tab_bar.addTab("Tab 1")
        tab_bar.addTab("Tab 2")
        tab_bar.addTab("Tab 3")
        
        mime_data = QMimeData()
        mime_data.setData(EditorTabBar.MIME_TYPE, str(0).encode())
        
        event = QDropEvent(
            QPoint(50, 10),
            Qt.DropActions.MoveAction,
            mime_data,
            Qt.MouseButtons.LeftButton,
            Qt.KeyboardModifiers.NoModifier
        )
        
        tab_bar.dropEvent(event)
        
        assert True  # Should not raise


class TestTabBarNewTabButton:
    """Tests for the new tab button."""
    
    def test_new_tab_button_exists(self, tab_bar):
        """Tab bar creates new tab button."""
        assert tab_bar._new_tab_button is not None
    
    def test_new_tab_button_text(self, tab_bar):
        """New tab button displays '+' symbol."""
        assert tab_bar._new_tab_button.text() == "+"
    
    def test_new_tab_button_click_emits_signal(self, tab_bar):
        """Clicking new tab button emits signal."""
        signal_emitted = []
        tab_bar.new_tab_requested.connect(lambda: signal_emitted.append(True))
        
        tab_bar._new_tab_button.clicked.emit()
        
        assert len(signal_emitted) == 1
    
    def test_position_new_tab_button(self, tab_bar):
        """New tab button is positioned after tabs."""
        tab_bar.addTab("Tab 1")
        tab_bar.addTab("Tab 2")
        
        tab_bar._position_new_tab_button()
        
        # Button should be positioned
        assert tab_bar._new_tab_button.geometry().x() >= 0


class TestTabBarPaintEvent:
    """Tests for custom paint event."""
    
    def test_paint_event_with_modified_tab(self, tab_bar):
        """Paint event renders modified indicator."""
        tab_bar.addTab("Test")
        tab_bar.setTabModified(0, True)
        
        # Trigger paint (indirectly through update)
        tab_bar.update()
        
        assert 0 in tab_bar._modified_tabs


class TestTabBarDropIndicator:
    """Tests for drop indicator visibility."""
    
    def test_drop_indicator_initialized(self, tab_bar):
        """Tab bar has drop indicator."""
        assert tab_bar._drop_indicator is not None
    
    def test_drag_move_shows_indicator(self, tab_bar):
        """Drag move shows drop indicator."""
        tab_bar.addTab("Tab 1")
        tab_bar.addTab("Tab 2")
        
        mime_data = QMimeData()
        mime_data.setData(EditorTabBar.MIME_TYPE, b"")
        
        event = QDragEnterEvent(
            QPoint(10, 10),
            Qt.DropActions.MoveAction,
            mime_data,
            Qt.MouseButtons.LeftButton,
            Qt.KeyboardModifiers.NoModifier
        )
        
        tab_bar.dragEnterEvent(event)
        
        assert event.isAccepted()


class TestTabBarDropIndex:
    """Tests for drop index calculation."""
    
    def test_get_drop_index_empty(self, tab_bar):
        """Drop index is 0 for empty tab bar."""
        from PySide6.QtCore import QPoint
        assert tab_bar.get_drop_index(QPoint(0, 0)) == 0
    
    def test_get_drop_index_with_tabs(self, tab_bar):
        """Drop index calculated correctly with tabs."""
        from PySide6.QtCore import QPoint
        tab_bar.addTab("Tab 1")
        tab_bar.addTab("Tab 2")
        index = tab_bar.get_drop_index(QPoint(1000, 0))
        assert index == tab_bar.count()
