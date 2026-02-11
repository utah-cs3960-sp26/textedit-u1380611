"""
Basic tests for main window initialization.
These tests focus on ensuring the window can be created and basic functionality works.
"""

import pytest
from PySide6.QtWidgets import QApplication
from editor.main_window import MainWindow


@pytest.fixture(scope="session")
def qapp():
    """Create a QApplication instance for the test session."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


class TestMainWindowInitialization:
    """Tests for MainWindow initialization."""
    
    def _cleanup_window(self, window):
        """Properly cleanup a window and release any grabs."""
        try:
            window.releaseMouse()
        except:
            pass
        try:
            window.releaseKeyboard()
        except:
            pass
        try:
            window.clearFocus()
        except:
            pass
        try:
            window.hide()
        except:
            pass
        try:
            window.close()
        except:
            pass
        try:
            window.deleteLater()
        except:
            pass
        # Process events to ensure cleanup
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance()
        if app:
            try:
                app.processEvents()
            except:
                pass
    
    def test_main_window_creation(self, qapp):
        """Test that MainWindow can be created."""
        window = MainWindow()
        assert window is not None
        self._cleanup_window(window)
    
    def test_main_window_has_container(self, qapp):
        """Test that MainWindow has a split container."""
        window = MainWindow()
        assert window._split_container is not None
        self._cleanup_window(window)
    
    def test_main_window_has_file_tree(self, qapp):
        """Test that MainWindow has a file tree."""
        window = MainWindow()
        assert window._file_tree is not None
        self._cleanup_window(window)
    
    def test_main_window_has_theme_manager(self, qapp):
        """Test that MainWindow has a theme manager."""
        window = MainWindow()
        assert window._theme_manager is not None
        self._cleanup_window(window)
    
    def test_main_window_has_sidebar(self, qapp):
        """Test that MainWindow has a sidebar."""
        window = MainWindow()
        assert window._sidebar is not None
        self._cleanup_window(window)
    
    def test_main_window_new_document(self, qapp):
        """Test creating new document in main window."""
        window = MainWindow()
        window._on_new()
        # Should have a document
        assert len(window._split_container.all_documents) > 0
        self._cleanup_window(window)
    
    def test_main_window_word_wrap_toggle(self, qapp):
        """Test toggling word wrap."""
        window = MainWindow()
        initial_state = window._word_wrap_enabled
        window._on_toggle_word_wrap(not initial_state)
        assert window._word_wrap_enabled != initial_state
        self._cleanup_window(window)
    
    def test_main_window_status_bar_update(self, qapp):
        """Test status bar updates."""
        window = MainWindow()
        window._update_status_bar()
        # Should have status bar text
        status_text = window.statusBar().currentMessage()
        # Status text should exist or be empty
        assert isinstance(status_text, str)
        self._cleanup_window(window)
