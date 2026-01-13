"""
Tests for the EditorTabBar module.
"""

import pytest
from PySide6.QtWidgets import QApplication

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
