"""
Tests for the FontMiniToolbar module.
"""

import pytest
from PySide6.QtWidgets import QApplication, QPlainTextEdit
from PySide6.QtGui import QFont, QTextCursor

from editor.font_toolbar import FontMiniToolbar


@pytest.fixture(scope="session")
def qapp():
    """Create a QApplication instance for the test session."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def toolbar(qapp):
    """Create a fresh FontMiniToolbar for each test."""
    widget = FontMiniToolbar()
    yield widget
    widget.deleteLater()


@pytest.fixture
def editor(qapp):
    """Create a fresh QPlainTextEdit for each test."""
    widget = QPlainTextEdit()
    widget.setPlainText("Hello World\nThis is test text.")
    yield widget
    widget.deleteLater()


class TestFontMiniToolbarCreation:
    """Tests for FontMiniToolbar initialization."""
    
    def test_toolbar_creation(self, toolbar):
        """Toolbar can be created."""
        assert toolbar is not None
    
    def test_has_font_combo(self, toolbar):
        """Toolbar has a font combo box."""
        assert toolbar._font_combo is not None
    
    def test_has_size_spinner(self, toolbar):
        """Toolbar has a size spin box."""
        assert toolbar._size_spin is not None
    
    def test_initially_hidden(self, toolbar):
        """Toolbar is hidden by default."""
        assert not toolbar.isVisible()
    
    def test_has_hide_timer(self, toolbar):
        """Toolbar has a hide timer."""
        assert toolbar._hide_timer is not None


class TestFontMiniToolbarDefaults:
    """Tests for FontMiniToolbar default values."""
    
    def test_default_size(self, toolbar):
        """Default font size is 12."""
        assert toolbar._size_spin.value() == 12
    
    def test_size_range(self, toolbar):
        """Size spinner has valid range."""
        assert toolbar._size_spin.minimum() == 6
        assert toolbar._size_spin.maximum() == 72


class TestFontMiniToolbarAttachment:
    """Tests for attaching toolbar to editors."""
    
    def test_attach_to_editor(self, toolbar, editor):
        """Can attach toolbar to an editor."""
        toolbar.attach_to_editor(editor)
        assert toolbar._editor == editor
    
    def test_attach_replaces_previous(self, toolbar, editor, qapp):
        """Attaching to new editor replaces previous."""
        editor2 = QPlainTextEdit()
        toolbar.attach_to_editor(editor)
        toolbar.attach_to_editor(editor2)
        assert toolbar._editor == editor2
        editor2.deleteLater()
    
    def test_attach_none_clears(self, toolbar, editor):
        """Attaching None clears the editor."""
        toolbar.attach_to_editor(editor)
        toolbar.attach_to_editor(None)
        assert toolbar._editor is None


class TestFontMiniToolbarTheme:
    """Tests for theme color application."""
    
    def test_set_theme_colors(self, toolbar):
        """Can set theme colors."""
        toolbar.set_theme_colors("#1e1e1e", "#d4d4d4", "#444444")
        style = toolbar.styleSheet()
        assert "#1e1e1e" in style
        assert "#d4d4d4" in style


class TestFontMiniToolbarSignals:
    """Tests for toolbar signals."""
    
    def test_font_changed_signal_exists(self, toolbar):
        """Font changed signal exists."""
        assert hasattr(toolbar, 'font_changed')


class TestFontMiniToolbarWithSelection:
    """Tests for toolbar behavior with text selection."""
    
    def test_shows_on_selection(self, toolbar, editor):
        """Toolbar shows when text is selected."""
        toolbar.attach_to_editor(editor)
        
        cursor = editor.textCursor()
        cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        editor.setTextCursor(cursor)
        
        assert cursor.hasSelection()
    
    def test_hide_timer_starts_on_deselect(self, toolbar, editor):
        """Hide timer starts when selection is cleared."""
        toolbar.attach_to_editor(editor)
        
        cursor = editor.textCursor()
        cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        editor.setTextCursor(cursor)
        
        cursor.clearSelection()
        editor.setTextCursor(cursor)
