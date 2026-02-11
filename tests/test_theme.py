"""
Tests for the ThemeManager module.
"""

import os
import json
import pytest
from pathlib import Path
from PySide6.QtWidgets import QApplication

from editor.theme_manager import (
    ThemeManager, Theme, 
    DARK_STYLESHEET, LIGHT_STYLESHEET,
    AQUAMARINE_STYLESHEET, MIDNIGHT_BLUE_STYLESHEET
)


@pytest.fixture(scope="session")
def qapp():
    """Create a QApplication instance for the test session."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def theme_manager(qapp):
    """Create a fresh ThemeManager for each test."""
    manager = ThemeManager()
    yield manager


class TestThemeEnum:
    """Tests for Theme enum."""
    
    def test_dark_theme_value(self):
        """Dark theme has correct value."""
        assert Theme.DARK.value == "dark"
    
    def test_light_theme_value(self):
        """Light theme has correct value."""
        assert Theme.LIGHT.value == "light"
    
    def test_aquamarine_theme_value(self):
        """Aquamarine theme has correct value."""
        assert Theme.AQUAMARINE.value == "aquamarine"
    
    def test_midnight_blue_theme_value(self):
        """Midnight Blue theme has correct value."""
        assert Theme.MIDNIGHT_BLUE.value == "midnight_blue"


class TestThemeManager:
    """Tests for ThemeManager."""
    
    def test_singleton_pattern(self, qapp):
        """ThemeManager is a singleton."""
        manager1 = ThemeManager()
        manager2 = ThemeManager()
        assert manager1 is manager2
    
    def test_apply_dark_theme(self, theme_manager, qapp):
        """Can apply dark theme."""
        theme_manager.apply_theme(Theme.DARK)
        assert theme_manager.current_theme == Theme.DARK
    
    def test_apply_light_theme(self, theme_manager, qapp):
        """Can apply light theme."""
        theme_manager.apply_theme(Theme.LIGHT)
        assert theme_manager.current_theme == Theme.LIGHT
    
    def test_toggle_theme_from_dark(self, theme_manager, qapp):
        """Toggle from dark switches to light."""
        theme_manager.apply_theme(Theme.DARK)
        theme_manager.toggle_theme()
        assert theme_manager.current_theme == Theme.LIGHT
    
    def test_toggle_theme_from_light(self, theme_manager, qapp):
        """Toggle from light switches to dark."""
        theme_manager.apply_theme(Theme.LIGHT)
        theme_manager.toggle_theme()
        assert theme_manager.current_theme == Theme.DARK
    
    def test_apply_aquamarine_theme(self, theme_manager, qapp):
        """Can apply aquamarine theme."""
        theme_manager.apply_theme(Theme.AQUAMARINE)
        assert theme_manager.current_theme == Theme.AQUAMARINE
    
    def test_apply_midnight_blue_theme(self, theme_manager, qapp):
        """Can apply midnight blue theme."""
        theme_manager.apply_theme(Theme.MIDNIGHT_BLUE)
        assert theme_manager.current_theme == Theme.MIDNIGHT_BLUE


class TestStylesheets:
    """Tests for stylesheet content."""
    
    def test_dark_stylesheet_not_empty(self):
        """Dark stylesheet has content."""
        assert len(DARK_STYLESHEET) > 0
    
    def test_light_stylesheet_not_empty(self):
        """Light stylesheet has content."""
        assert len(LIGHT_STYLESHEET) > 0
    
    def test_dark_stylesheet_has_dark_colors(self):
        """Dark stylesheet uses dark background colors."""
        assert "#1e1e1e" in DARK_STYLESHEET
        assert "#2d2d2d" in DARK_STYLESHEET
    
    def test_light_stylesheet_has_light_colors(self):
        """Light stylesheet uses light background colors."""
        assert "#ffffff" in LIGHT_STYLESHEET
        assert "#f3f3f3" in LIGHT_STYLESHEET
    
    def test_stylesheets_have_status_bar_accent(self):
        """All stylesheets have status bar accent colors."""
        assert "#007acc" in DARK_STYLESHEET
        assert "#0078d4" in LIGHT_STYLESHEET
        assert "#40e0d0" in AQUAMARINE_STYLESHEET
        assert "#238636" in MIDNIGHT_BLUE_STYLESHEET
    
    def test_aquamarine_stylesheet_not_empty(self):
        """Aquamarine stylesheet has content."""
        assert len(AQUAMARINE_STYLESHEET) > 0
    
    def test_midnight_blue_stylesheet_not_empty(self):
        """Midnight Blue stylesheet has content."""
        assert len(MIDNIGHT_BLUE_STYLESHEET) > 0
    
    def test_aquamarine_has_turquoise_colors(self):
        """Aquamarine stylesheet uses turquoise colors."""
        assert "#40e0d0" in AQUAMARINE_STYLESHEET
        assert "#1a2f2f" in AQUAMARINE_STYLESHEET
    
    def test_aquamarine_has_orange_accent(self):
        """Aquamarine stylesheet uses orange accent."""
        assert "#ff8c42" in AQUAMARINE_STYLESHEET
    
    def test_midnight_blue_has_dark_blue_background(self):
        """Midnight Blue stylesheet uses dark blue background."""
        assert "#0d1117" in MIDNIGHT_BLUE_STYLESHEET
        assert "#161b22" in MIDNIGHT_BLUE_STYLESHEET
    
    def test_midnight_blue_has_bright_accents(self):
        """Midnight Blue stylesheet has bright accent colors."""
        assert "#58a6ff" in MIDNIGHT_BLUE_STYLESHEET
        assert "#f85149" in MIDNIGHT_BLUE_STYLESHEET


class TestThemeErrorHandling:
    """Tests for error handling in theme loading and saving."""
    
    def test_custom_theme_names_with_no_custom_themes(self, theme_manager):
        """get_custom_theme_names returns empty list when no custom themes exist."""
        custom_names = theme_manager.get_custom_theme_names()
        assert isinstance(custom_names, list)
        # Should be empty or contain only existing custom themes
        assert all(isinstance(name, str) for name in custom_names)
    
    def test_save_custom_theme_creates_theme(self, theme_manager, tmp_path, monkeypatch):
        """save_custom_theme adds theme to manager."""
        # Mock the themes directory
        monkeypatch.setenv("HOME", str(tmp_path))
        
        theme_manager.save_custom_theme("Test Theme", {"bg": "#ffffff"})
        
        custom_names = theme_manager.get_custom_theme_names()
        assert "Test Theme" in custom_names
    
    def test_get_theme_colors_fallback_to_dark(self, theme_manager):
        """get_theme_colors falls back to Dark theme for unknown themes."""
        colors = theme_manager.get_theme_colors("NonexistentTheme")
        
        # Should return Dark theme colors as fallback
        dark_colors = theme_manager.get_theme_colors("Dark")
        assert colors == dark_colors


class TestCustomThemeFileIO:
    """Tests for custom theme file I/O operations."""
    
    def test_save_custom_theme_writes_json_file(self, theme_manager, tmp_path, monkeypatch):
        """save_custom_theme writes theme to JSON file."""
        monkeypatch.setenv("HOME", str(tmp_path))
        
        colors = {"bg": "#000000", "text": "#ffffff", "accent": "#0078d4"}
        theme_manager.save_custom_theme("CustomTheme", colors)
        
        themes_dir = tmp_path / ".textedit" / "themes"
        theme_file = themes_dir / "CustomTheme.json"
        assert theme_file.exists()
        
        # Verify file contents
        data = json.loads(theme_file.read_text())
        assert data["name"] == "CustomTheme"
        assert data["colors"] == colors
    
    def test_save_custom_theme_with_special_characters_in_name(self, theme_manager, tmp_path, monkeypatch):
        """save_custom_theme sanitizes theme names with special characters."""
        monkeypatch.setenv("HOME", str(tmp_path))
        
        # Use name with special characters
        theme_manager.save_custom_theme("My-Custom_Theme", {"bg": "#111111"})
        
        themes_dir = tmp_path / ".textedit" / "themes"
        # Should create a file with sanitized name
        assert (themes_dir / "My-Custom_Theme.json").exists()
    
    def test_save_custom_theme_io_error_handling(self, theme_manager, monkeypatch):
        """save_custom_theme handles IOError gracefully."""
        def failing_open(*args, **kwargs):
            raise IOError("Permission denied")
        
        monkeypatch.setattr("builtins.open", failing_open)
        # Should not raise exception
        theme_manager.save_custom_theme("Test", {"bg": "#000"})
        assert True  # Made it without exception
    
    def test_delete_custom_theme_removes_file(self, theme_manager, tmp_path, monkeypatch):
        """delete_custom_theme removes the theme file."""
        monkeypatch.setenv("HOME", str(tmp_path))
        
        # First save a theme
        theme_manager.save_custom_theme("ToDelete", {"bg": "#222222"})
        themes_dir = tmp_path / ".textedit" / "themes"
        theme_file = themes_dir / "ToDelete.json"
        assert theme_file.exists()
        
        # Delete it
        theme_manager.delete_custom_theme("ToDelete")
        assert not theme_file.exists()
        assert "ToDelete" not in theme_manager.get_custom_theme_names()
    
    def test_delete_custom_theme_io_error_handling(self, theme_manager, monkeypatch):
        """delete_custom_theme handles IOError gracefully."""
        theme_manager._custom_themes["Temp"] = {"bg": "#000"}
        
        def failing_remove(*args, **kwargs):
            raise IOError("Cannot delete")
        
        monkeypatch.setattr("os.remove", failing_remove)
        # Should not raise exception
        theme_manager.delete_custom_theme("Temp")
        assert True  # Made it without exception
    
    def test_delete_nonexistent_custom_theme(self, theme_manager):
        """delete_custom_theme does nothing for nonexistent themes."""
        initial_count = len(theme_manager.get_custom_theme_names())
        theme_manager.delete_custom_theme("DoesNotExist")
        assert len(theme_manager.get_custom_theme_names()) == initial_count
    
    def test_get_theme_colors_returns_copy(self, theme_manager):
        """get_theme_colors returns a copy, not reference."""
        theme_manager._custom_themes["Original"] = {"bg": "#555555"}
        
        colors1 = theme_manager.get_theme_colors("Original")
        colors2 = theme_manager.get_theme_colors("Original")
        
        # Modify one copy
        colors1["bg"] = "#999999"
        
        # Other should be unchanged
        assert colors2["bg"] == "#555555"


class TestLoadSettingsErrorHandling:
    """Tests for loading settings with error conditions."""
    
    def test_load_settings_with_malformed_json(self, tmp_path, monkeypatch):
        """_load_settings handles malformed JSON gracefully."""
        import importlib
        import sys
        
        monkeypatch.setenv("HOME", str(tmp_path))
        settings_dir = tmp_path / ".textedit"
        settings_dir.mkdir(parents=True, exist_ok=True)
        
        # Write invalid JSON
        (settings_dir / "settings.json").write_text("{invalid json content")
        
        # Reset singleton
        ThemeManager._instance = None
        manager = ThemeManager()
        assert manager is not None
    
    def test_load_settings_with_missing_file(self, tmp_path, monkeypatch):
        """_load_settings handles missing settings file gracefully."""
        monkeypatch.setenv("HOME", str(tmp_path))
        
        # Reset singleton
        ThemeManager._instance = None
        manager = ThemeManager()
        # Should use default theme
        assert manager.current_theme_name == "Midnight Blue"
    
    def test_load_custom_themes_with_invalid_json_files(self, tmp_path, monkeypatch):
        """_load_custom_themes skips invalid JSON files."""
        monkeypatch.setenv("HOME", str(tmp_path))
        themes_dir = tmp_path / ".textedit" / "themes"
        themes_dir.mkdir(parents=True, exist_ok=True)
        
        # Create invalid JSON file
        (themes_dir / "invalid.json").write_text("{not valid json}")
        
        # Create valid JSON file
        valid_theme = {"name": "Valid", "colors": {"bg": "#000"}}
        (themes_dir / "valid.json").write_text(json.dumps(valid_theme))
        
        # Reset singleton
        ThemeManager._instance = None
        manager = ThemeManager()
        custom_names = manager.get_custom_theme_names()
        
        # Valid theme should load, invalid should be skipped
        assert "Valid" in custom_names
    
    def test_save_settings_io_error_handling(self, theme_manager, monkeypatch):
        """_save_settings handles IOError gracefully."""
        def failing_open(*args, **kwargs):
            raise IOError("Cannot write")
        
        monkeypatch.setattr("builtins.open", failing_open)
        # Should not raise exception
        theme_manager._save_settings()
        assert True  # Made it without exception
    
    def test_delete_custom_theme_with_io_error(self, theme_manager, monkeypatch, tmp_path):
        """delete_custom_theme handles IOError/KeyError gracefully."""
        monkeypatch.setenv("HOME", str(tmp_path))
        themes_dir = tmp_path / ".textedit" / "themes"
        themes_dir.mkdir(parents=True, exist_ok=True)
        
        # Reset singleton
        ThemeManager._instance = None
        manager = ThemeManager()
        
        # Mock os.remove to raise IOError
        original_remove = os.remove
        def failing_remove(path):
            raise IOError("Cannot delete")
        
        monkeypatch.setattr("os.remove", failing_remove)
        
        # Should not raise exception even if remove fails
        manager.delete_custom_theme("NonExistent")
        assert True  # Made it without exception
    
    def test_get_builtin_theme_names(self, theme_manager):
        """get_builtin_theme_names returns list of builtin themes."""
        names = theme_manager.get_builtin_theme_names()
        
        assert isinstance(names, list)
        assert "Dark" in names
        assert "Light" in names
        assert len(names) > 0
    
    def test_get_line_number_colors(self, theme_manager):
        """get_line_number_colors returns color dictionary."""
        theme_manager.apply_theme(Theme.DARK)
        colors = theme_manager.get_line_number_colors()
        
        assert isinstance(colors, dict)
        assert "bg" in colors
        assert "text" in colors
        assert "current_line" in colors
        assert "current_line_bg" in colors
