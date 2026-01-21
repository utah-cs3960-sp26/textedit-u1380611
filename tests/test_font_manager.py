"""
Tests for the FontManagerWidget in settings_dialog.
"""

import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont

from editor.settings_dialog import FontManagerWidget, FontManagerDialog
from editor.theme_manager import ThemeManager


@pytest.fixture(scope="session")
def qapp():
    """Create a QApplication instance for the test session."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def font_widget(qapp):
    """Create a fresh FontManagerWidget for each test."""
    widget = FontManagerWidget()
    yield widget
    widget.deleteLater()


@pytest.fixture
def font_dialog(qapp):
    """Create a fresh FontManagerDialog for each test."""
    theme_manager = ThemeManager()
    dialog = FontManagerDialog(theme_manager)
    yield dialog
    dialog.deleteLater()


class TestFontManagerWidgetCreation:
    """Tests for FontManagerWidget initialization."""
    
    def test_widget_creation(self, font_widget):
        """FontManagerWidget can be created."""
        assert font_widget is not None
    
    def test_has_font_combo(self, font_widget):
        """Widget has a font combo box."""
        assert font_widget._font_combo is not None
    
    def test_has_size_spinner(self, font_widget):
        """Widget has a size spin box."""
        assert font_widget._size_spin is not None
    
    def test_has_preview_text(self, font_widget):
        """Widget has a preview text area."""
        assert font_widget._preview_text is not None
    
    def test_has_apply_button(self, font_widget):
        """Widget has an apply button."""
        assert font_widget._apply_btn is not None
    
    def test_has_radio_buttons(self, font_widget):
        """Widget has radio buttons for apply mode."""
        assert font_widget._apply_all_radio is not None
        assert font_widget._apply_selection_radio is not None


class TestFontManagerDefaults:
    """Tests for FontManagerWidget default values."""
    
    def test_default_size(self, font_widget):
        """Default font size is 12."""
        assert font_widget._size_spin.value() == 12
    
    def test_default_apply_all(self, font_widget):
        """Default apply mode is 'all text'."""
        assert font_widget._apply_all_radio.isChecked()
        assert not font_widget._apply_selection_radio.isChecked()
    
    def test_size_range(self, font_widget):
        """Size spinner has valid range."""
        assert font_widget._size_spin.minimum() == 6
        assert font_widget._size_spin.maximum() == 72


class TestFontSelection:
    """Tests for font selection functionality."""
    
    def test_get_current_font(self, font_widget):
        """Can get the current font."""
        font = font_widget.get_current_font()
        assert isinstance(font, QFont)
    
    def test_font_has_correct_size(self, font_widget):
        """Current font has the correct size."""
        font_widget._size_spin.setValue(16)
        font = font_widget.get_current_font()
        assert font.pointSize() == 16
    
    def test_is_selection_mode_default(self, font_widget):
        """Selection mode is False by default."""
        assert font_widget.is_selection_mode() is False
    
    def test_is_selection_mode_when_selected(self, font_widget):
        """Selection mode is True when radio is checked."""
        font_widget._apply_selection_radio.setChecked(True)
        assert font_widget.is_selection_mode() is True


class TestFontPreview:
    """Tests for font preview functionality."""
    
    def test_preview_has_sample_text(self, font_widget):
        """Preview area has sample text."""
        text = font_widget._preview_text.toPlainText()
        assert len(text) > 0
        assert "quick brown fox" in text
    
    def test_preview_updates_with_font(self, font_widget):
        """Preview updates when font changes."""
        original_font = font_widget._preview_text.font()
        font_widget._size_spin.setValue(24)
        new_font = font_widget._preview_text.font()
        assert new_font.pointSize() == 24


class TestFontSignals:
    """Tests for font apply signal."""
    
    def test_signal_exists(self, font_widget):
        """Font apply signal exists."""
        assert hasattr(font_widget, 'font_apply_requested')
    
    def test_signal_emitted_on_apply(self, font_widget):
        """Signal is emitted when apply button clicked."""
        received = []
        font_widget.font_apply_requested.connect(
            lambda f, s: received.append((f, s))
        )
        font_widget._apply_btn.click()
        assert len(received) == 1
    
    def test_signal_contains_font(self, font_widget):
        """Signal contains the selected font."""
        font_widget._size_spin.setValue(18)
        
        received = []
        font_widget.font_apply_requested.connect(
            lambda f, s: received.append((f, s))
        )
        font_widget._apply_btn.click()
        
        assert len(received) == 1
        font, selection_only = received[0]
        assert isinstance(font, QFont)
        assert font.pointSize() == 18
        assert selection_only is False
    
    def test_signal_contains_selection_flag(self, font_widget):
        """Signal contains selection_only flag."""
        font_widget._apply_selection_radio.setChecked(True)
        
        received = []
        font_widget.font_apply_requested.connect(
            lambda f, s: received.append((f, s))
        )
        font_widget._apply_btn.click()
        
        assert len(received) == 1
        _, selection_only = received[0]
        assert selection_only is True


class TestFontThemeIntegration:
    """Tests for theme color integration in FontManagerWidget."""
    
    def test_set_theme_colors(self, font_widget):
        """Can set theme colors."""
        font_widget.set_theme_colors("#000000", "#ffffff")
        assert font_widget._editor_bg == "#000000"
        assert font_widget._editor_text == "#ffffff"
    
    def test_preview_style_applied(self, font_widget):
        """Preview has stylesheet applied."""
        font_widget.set_theme_colors("#1a2f2f", "#e0f0f0")
        style = font_widget._preview_text.styleSheet()
        assert "#1a2f2f" in style
        assert "#e0f0f0" in style


class TestFontManagerDialog:
    """Tests for FontManagerDialog."""
    
    def test_dialog_creation(self, font_dialog):
        """FontManagerDialog can be created."""
        assert font_dialog is not None
    
    def test_has_font_widget(self, font_dialog):
        """Dialog has a font widget."""
        assert font_dialog._font_widget is not None
    
    def test_has_theme_manager(self, font_dialog):
        """Dialog has a theme manager."""
        assert font_dialog._theme_manager is not None
    
    def test_font_signal_exists(self, font_dialog):
        """Dialog has font apply signal."""
        assert hasattr(font_dialog, 'font_apply_requested')
    
    def test_font_signal_forwarded(self, font_dialog):
        """Font signal is forwarded from widget to dialog."""
        received = []
        font_dialog.font_apply_requested.connect(
            lambda f, s: received.append((f, s))
        )
        
        font_dialog._font_widget._apply_btn.click()
        
        assert len(received) == 1
    
    def test_window_title(self, font_dialog):
        """Dialog has correct window title."""
        assert font_dialog.windowTitle() == "Font Manager"
    
    def test_theme_colors_applied(self, font_dialog):
        """Theme colors are applied to font widget."""
        style = font_dialog._font_widget._preview_text.styleSheet()
        assert len(style) > 0
