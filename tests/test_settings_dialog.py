"""
Tests for the Settings Dialog and Theme Manager enhancements.
"""

import os
import json
import tempfile
import pytest
from unittest.mock import patch, MagicMock
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from editor.settings_dialog import (
    ColorButton, ThemeEditorWidget, ThemeManagerWidget, SettingsDialog
)
from editor.theme_manager import (
    ThemeManager, Theme, BUILTIN_THEME_COLORS,
    generate_stylesheet_from_colors, get_themes_dir, get_settings_path
)


@pytest.fixture(scope="session")
def qapp():
    """Create a QApplication instance for the test session."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


class TestColorButton:
    """Tests for ColorButton widget."""
    
    def test_initial_color(self, qapp):
        """Test button initializes with specified color."""
        btn = ColorButton("#ff0000")
        assert btn.color == "#ff0000"
        btn.deleteLater()
    
    def test_default_color(self, qapp):
        """Test button defaults to white."""
        btn = ColorButton()
        assert btn.color == "#ffffff"
        btn.deleteLater()
    
    def test_set_color(self, qapp):
        """Test setting color property."""
        btn = ColorButton()
        btn.color = "#00ff00"
        assert btn.color == "#00ff00"
        btn.deleteLater()
    
    def test_color_changed_signal_exists(self, qapp):
        """Test color_changed signal exists."""
        btn = ColorButton()
        assert hasattr(btn, 'color_changed')
        btn.deleteLater()


class TestThemeEditorWidget:
    """Tests for ThemeEditorWidget."""
    
    def test_creation(self, qapp):
        """Test widget creates successfully."""
        editor = ThemeEditorWidget()
        assert editor is not None
        editor.deleteLater()
    
    def test_get_colors_returns_dict(self, qapp):
        """Test get_colors returns a dictionary."""
        editor = ThemeEditorWidget()
        colors = editor.get_colors()
        assert isinstance(colors, dict)
        editor.deleteLater()
    
    def test_set_colors(self, qapp):
        """Test set_colors applies colors."""
        editor = ThemeEditorWidget()
        test_colors = {
            "editor_background": "#123456",
            "editor_text": "#abcdef"
        }
        editor.set_colors(test_colors)
        colors = editor.get_colors()
        assert colors.get("editor_background") == "#123456"
        assert colors.get("editor_text") == "#abcdef"
        editor.deleteLater()
    
    def test_has_color_fields(self, qapp):
        """Test COLOR_FIELDS is defined."""
        assert hasattr(ThemeEditorWidget, 'COLOR_FIELDS')
        assert len(ThemeEditorWidget.COLOR_FIELDS) > 0
        editor = ThemeEditorWidget()
        editor.deleteLater()
    
    def test_theme_modified_signal_exists(self, qapp):
        """Test theme_modified signal exists."""
        editor = ThemeEditorWidget()
        assert hasattr(editor, 'theme_modified')
        editor.deleteLater()


class TestThemeManagerEnhancements:
    """Tests for ThemeManager custom theme support."""
    
    def test_get_builtin_theme_names(self, qapp):
        """Test getting built-in theme names."""
        manager = ThemeManager()
        names = manager.get_builtin_theme_names()
        assert "Dark" in names
        assert "Light" in names
        assert "Aquamarine" in names
        assert "Midnight Blue" in names
    
    def test_get_theme_colors_builtin(self, qapp):
        """Test getting colors for built-in theme."""
        manager = ThemeManager()
        colors = manager.get_theme_colors("Dark")
        assert "editor_background" in colors
        assert "editor_text" in colors
        assert colors["editor_background"] == "#1e1e1e"
    
    def test_get_theme_colors_fallback(self, qapp):
        """Test fallback to Dark for unknown theme."""
        manager = ThemeManager()
        colors = manager.get_theme_colors("NonexistentTheme")
        assert colors == BUILTIN_THEME_COLORS["Dark"]
    
    def test_current_theme_name_property(self, qapp):
        """Test current_theme_name property."""
        manager = ThemeManager()
        assert manager.current_theme_name is not None
        assert isinstance(manager.current_theme_name, str)
    
    def test_apply_theme_by_name(self, qapp):
        """Test applying theme by name."""
        manager = ThemeManager()
        manager.apply_theme_by_name("Light")
        assert manager.current_theme_name == "Light"
        assert manager.current_theme == Theme.LIGHT
        manager.apply_theme_by_name("Midnight Blue")
    
    def test_custom_theme_enum_value(self, qapp):
        """Test CUSTOM theme enum exists."""
        assert Theme.CUSTOM.value == "custom"


class TestCustomThemePersistence:
    """Tests for custom theme save/load."""
    
    def test_save_custom_theme(self, qapp, tmp_path):
        """Test saving a custom theme."""
        with patch('editor.theme_manager.get_themes_dir', return_value=str(tmp_path)):
            manager = ThemeManager()
            manager._custom_themes = {}
            
            colors = {"editor_background": "#112233", "editor_text": "#aabbcc"}
            manager.save_custom_theme("TestTheme", colors)
            
            assert "TestTheme" in manager._custom_themes
            assert manager._custom_themes["TestTheme"]["editor_background"] == "#112233"
    
    def test_delete_custom_theme(self, qapp, tmp_path):
        """Test deleting a custom theme."""
        with patch('editor.theme_manager.get_themes_dir', return_value=str(tmp_path)):
            manager = ThemeManager()
            manager._custom_themes = {}
            
            colors = {"editor_background": "#112233"}
            manager.save_custom_theme("ToDelete", colors)
            assert "ToDelete" in manager._custom_themes
            
            manager.delete_custom_theme("ToDelete")
            assert "ToDelete" not in manager._custom_themes
    
    def test_get_custom_theme_names(self, qapp):
        """Test getting custom theme names."""
        manager = ThemeManager()
        names = manager.get_custom_theme_names()
        assert isinstance(names, list)


class TestGenerateStylesheet:
    """Tests for stylesheet generation from colors."""
    
    def test_generates_non_empty_stylesheet(self):
        """Test that stylesheet is generated."""
        colors = BUILTIN_THEME_COLORS["Dark"]
        stylesheet = generate_stylesheet_from_colors(colors)
        assert len(stylesheet) > 0
    
    def test_stylesheet_contains_colors(self):
        """Test stylesheet contains the specified colors."""
        colors = {"editor_background": "#aabbcc", "editor_text": "#112233"}
        stylesheet = generate_stylesheet_from_colors(colors)
        assert "#aabbcc" in stylesheet
        assert "#112233" in stylesheet
    
    def test_stylesheet_has_all_widgets(self):
        """Test stylesheet includes styling for main widgets."""
        colors = BUILTIN_THEME_COLORS["Dark"]
        stylesheet = generate_stylesheet_from_colors(colors)
        assert "QMainWindow" in stylesheet
        assert "QMenuBar" in stylesheet
        assert "QPlainTextEdit" in stylesheet
        assert "QStatusBar" in stylesheet
        assert "QTabBar" in stylesheet
    
    def test_stylesheet_uses_defaults_for_missing(self):
        """Test stylesheet uses defaults for missing colors."""
        stylesheet = generate_stylesheet_from_colors({})
        assert "#1e1e1e" in stylesheet


class TestBuiltinThemeColors:
    """Tests for BUILTIN_THEME_COLORS structure."""
    
    def test_all_themes_have_required_colors(self):
        """Test all built-in themes have required color keys."""
        required_keys = [
            "main_background", "editor_background", "editor_text",
            "line_number_bg", "line_number_text"
        ]
        for theme_name, colors in BUILTIN_THEME_COLORS.items():
            for key in required_keys:
                assert key in colors, f"{theme_name} missing {key}"
    
    def test_dark_theme_has_dark_colors(self):
        """Test Dark theme uses dark background colors."""
        colors = BUILTIN_THEME_COLORS["Dark"]
        bg = colors["editor_background"]
        assert bg.startswith("#")
        r = int(bg[1:3], 16)
        g = int(bg[3:5], 16)
        b = int(bg[5:7], 16)
        avg = (r + g + b) / 3
        assert avg < 128
    
    def test_light_theme_has_light_colors(self):
        """Test Light theme uses light background colors."""
        colors = BUILTIN_THEME_COLORS["Light"]
        bg = colors["editor_background"]
        assert bg.startswith("#")
        r = int(bg[1:3], 16)
        g = int(bg[3:5], 16)
        b = int(bg[5:7], 16)
        avg = (r + g + b) / 3
        assert avg > 128


class TestSettingsDialog:
    """Tests for SettingsDialog."""
    
    def test_dialog_creation(self, qapp):
        """Test dialog creates successfully."""
        manager = ThemeManager()
        dialog = SettingsDialog(manager)
        assert dialog is not None
        dialog.deleteLater()
    
    def test_dialog_has_minimum_size(self, qapp):
        """Test dialog has reasonable minimum size."""
        manager = ThemeManager()
        dialog = SettingsDialog(manager)
        assert dialog.minimumWidth() >= 500
        assert dialog.minimumHeight() >= 400
        dialog.deleteLater()
    
    def test_theme_changed_signal_exists(self, qapp):
        """Test theme_changed signal exists."""
        manager = ThemeManager()
        dialog = SettingsDialog(manager)
        assert hasattr(dialog, 'theme_changed')
        dialog.deleteLater()


class TestThemeManagerWidget:
    """Tests for ThemeManagerWidget."""
    
    def test_widget_creation(self, qapp):
        """Test widget creates successfully."""
        manager = ThemeManager()
        widget = ThemeManagerWidget(manager)
        assert widget is not None
        widget.deleteLater()
    
    def test_theme_applied_signal_exists(self, qapp):
        """Test theme_applied signal exists."""
        manager = ThemeManager()
        widget = ThemeManagerWidget(manager)
        assert hasattr(widget, 'theme_applied')
        widget.deleteLater()
    
    def test_loads_builtin_themes(self, qapp):
        """Test built-in themes are loaded into list."""
        manager = ThemeManager()
        widget = ThemeManagerWidget(manager)
        count = widget._theme_list.count()
        assert count >= 4
        widget.deleteLater()


class TestLineNumberColors:
    """Tests for line number color extraction."""
    
    def test_get_line_number_colors_from_builtin(self, qapp):
        """Test getting line number colors from theme."""
        manager = ThemeManager()
        manager.apply_theme_by_name("Dark")
        colors = manager.get_line_number_colors()
        assert "bg" in colors
        assert "text" in colors
        assert "current_line" in colors
        assert "current_line_bg" in colors
    
    def test_line_number_colors_match_theme(self, qapp):
        """Test line number colors match theme colors."""
        manager = ThemeManager()
        manager.apply_theme_by_name("Dark")
        colors = manager.get_line_number_colors()
        theme_colors = BUILTIN_THEME_COLORS["Dark"]
        assert colors["bg"] == theme_colors["line_number_bg"]
        assert colors["text"] == theme_colors["line_number_text"]
