"""
Tests for the ThemeManager module.
"""

import pytest
from PySide6.QtWidgets import QApplication

from editor.theme_manager import ThemeManager, Theme, DARK_STYLESHEET, LIGHT_STYLESHEET


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
        """Both stylesheets have blue status bar accent."""
        assert "#007acc" in DARK_STYLESHEET
        assert "#0078d4" in LIGHT_STYLESHEET
