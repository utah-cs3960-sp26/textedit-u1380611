"""
Targeted tests for missing coverage lines in editor/settings_dialog.py.

Covers lines: 283-284, 302, 331-354, 359, 363, 385, 395-415, 420-430, 605.
"""

import pytest
from unittest.mock import patch, MagicMock
from PySide6.QtWidgets import QApplication, QMessageBox, QListWidgetItem
from PySide6.QtCore import Qt

from editor.settings_dialog import ThemeManagerWidget, SettingsDialog
from editor.theme_manager import ThemeManager


@pytest.fixture(scope="session")
def qapp():
    """Create a QApplication instance for the test session."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def theme_manager():
    """Create a fresh ThemeManager instance (reset singleton)."""
    ThemeManager._instance = None
    tm = ThemeManager()
    yield tm
    # Clean up any custom themes created during tests
    for name in list(tm.get_custom_theme_names()):
        tm.delete_custom_theme(name)
    ThemeManager._instance = None


@pytest.fixture
def theme_widget(qapp, theme_manager):
    """Create a ThemeManagerWidget for testing."""
    widget = ThemeManagerWidget(theme_manager)
    yield widget
    widget.deleteLater()
    qapp.processEvents()


class TestThemeSelectionCancel:
    """Tests for lines 283-284: Cancel reverts selection when modified."""

    def test_cancel_reverts_to_previous_item(self, theme_widget):
        """When modified and user clicks Cancel, selection reverts to previous item."""
        # Select first theme
        assert theme_widget._theme_list.count() > 1
        first_item = theme_widget._theme_list.item(0)
        theme_widget._theme_list.setCurrentItem(first_item)
        theme_widget._is_modified = False

        # Set modified flag
        theme_widget._is_modified = True

        second_item = theme_widget._theme_list.item(1)

        with patch.object(QMessageBox, 'question', return_value=QMessageBox.StandardButton.Cancel):
            theme_widget._on_theme_selected(second_item, first_item)

        # Should revert to the first item
        assert theme_widget._theme_list.currentItem() == first_item


class TestThemeModifiedFlag:
    """Tests for line 302: _on_theme_modified sets _is_modified = True."""

    def test_on_theme_modified_sets_flag(self, theme_widget):
        """Calling _on_theme_modified() sets _is_modified to True."""
        theme_widget._is_modified = False
        theme_widget._on_theme_modified()
        assert theme_widget._is_modified is True


class TestDuplicateTheme:
    """Tests for lines 331-354: _on_duplicate_theme full method."""

    def test_duplicate_creates_copy(self, theme_widget, theme_manager):
        """Duplicating a theme creates a new theme with ' Copy' suffix."""
        # Select first theme
        first_item = theme_widget._theme_list.item(0)
        theme_widget._theme_list.setCurrentItem(first_item)
        theme_widget._is_modified = False

        original_name = theme_widget._current_theme_name
        original_count = theme_widget._theme_list.count()

        theme_widget._on_duplicate_theme()

        expected_name = f"{original_name} Copy"
        assert expected_name in theme_manager.get_custom_theme_names()
        assert theme_widget._theme_list.count() > original_count

        # Clean up
        theme_manager.delete_custom_theme(expected_name)

    def test_duplicate_with_no_current_theme(self, theme_widget):
        """Duplicating when _current_theme_name is None does nothing."""
        theme_widget._current_theme_name = None
        count_before = theme_widget._theme_list.count()
        theme_widget._on_duplicate_theme()
        assert theme_widget._theme_list.count() == count_before

    def test_duplicate_increments_counter_on_name_conflict(self, theme_widget, theme_manager):
        """Duplicate generates unique name when 'Copy' already exists."""
        first_item = theme_widget._theme_list.item(0)
        theme_widget._theme_list.setCurrentItem(first_item)
        theme_widget._is_modified = False
        original_name = theme_widget._current_theme_name

        # First duplicate
        theme_widget._on_duplicate_theme()
        # Select original again and duplicate again
        for i in range(theme_widget._theme_list.count()):
            item = theme_widget._theme_list.item(i)
            _, name = item.data(Qt.ItemDataRole.UserRole)
            if name == original_name:
                theme_widget._theme_list.setCurrentItem(item)
                theme_widget._is_modified = False
                break
        theme_widget._on_duplicate_theme()

        copy1 = f"{original_name} Copy"
        copy2 = f"{original_name} Copy 2"
        custom_names = theme_manager.get_custom_theme_names()
        assert copy1 in custom_names
        assert copy2 in custom_names

        # Clean up
        theme_manager.delete_custom_theme(copy1)
        theme_manager.delete_custom_theme(copy2)


class TestDeleteThemeEarlyReturns:
    """Tests for lines 359 and 363: early returns in _on_delete_theme."""

    def test_delete_no_current_theme_name(self, theme_widget):
        """Delete returns early when _current_theme_name is None (line 359)."""
        theme_widget._current_theme_name = None
        # Should not raise
        theme_widget._on_delete_theme()

    def test_delete_no_current_item(self, theme_widget):
        """Delete returns early when currentItem() is None (line 363)."""
        theme_widget._current_theme_name = "SomeName"
        theme_widget._theme_list.clearSelection()
        theme_widget._theme_list.setCurrentItem(None)

        # Should not raise
        theme_widget._on_delete_theme()


class TestSaveThemeEarlyReturn:
    """Tests for line 385: _on_save_theme returns early when no current item."""

    def test_save_no_current_item(self, theme_widget):
        """Save returns early when currentItem() is None (line 385)."""
        theme_widget._theme_list.clearSelection()
        theme_widget._theme_list.setCurrentItem(None)
        # Should not raise
        theme_widget._on_save_theme()


class TestSaveThemeCustom:
    """Tests for lines 395-415: Saving a custom theme."""

    def test_save_custom_theme(self, theme_widget, theme_manager):
        """Save a custom theme and verify it persists (lines 395-415)."""
        # Create a custom theme first
        theme_widget._on_new_theme()
        # Now current item should be the new custom theme
        current = theme_widget._theme_list.currentItem()
        assert current is not None
        theme_type, name = current.data(Qt.ItemDataRole.UserRole)
        assert theme_type == "custom"

        # Modify name and save
        theme_widget._name_edit.setText("My Saved Theme")
        theme_widget._on_save_theme()

        assert "My Saved Theme" in theme_manager.get_custom_theme_names()
        assert theme_widget._is_modified is False

        # Clean up
        theme_manager.delete_custom_theme("My Saved Theme")

    def test_save_renames_theme(self, theme_widget, theme_manager):
        """Renaming on save deletes old theme (lines 402-404)."""
        theme_manager.save_custom_theme("OldName", {"editor_background": "#111"})
        theme_widget._load_themes()

        # Select the custom theme
        for i in range(theme_widget._theme_list.count()):
            item = theme_widget._theme_list.item(i)
            t, n = item.data(Qt.ItemDataRole.UserRole)
            if n == "OldName":
                theme_widget._theme_list.setCurrentItem(item)
                theme_widget._is_modified = False
                break

        theme_widget._name_edit.setText("NewName")
        theme_widget._on_save_theme()

        assert "NewName" in theme_manager.get_custom_theme_names()
        assert "OldName" not in theme_manager.get_custom_theme_names()

        # Clean up
        theme_manager.delete_custom_theme("NewName")

    def test_save_empty_name_shows_warning(self, theme_widget, theme_manager):
        """Save with empty name shows warning (lines 396-398)."""
        theme_widget._on_new_theme()
        theme_widget._name_edit.setText("")

        with patch.object(QMessageBox, 'warning') as mock_warn:
            theme_widget._on_save_theme()
            mock_warn.assert_called_once()

        # Clean up created theme
        for name in list(theme_manager.get_custom_theme_names()):
            if name.startswith("Custom Theme"):
                theme_manager.delete_custom_theme(name)

    def test_save_builtin_theme_shows_info(self, theme_widget):
        """Saving a builtin theme shows information dialog (lines 388-393)."""
        # Select a builtin theme
        first_item = theme_widget._theme_list.item(0)
        theme_widget._theme_list.setCurrentItem(first_item)
        theme_widget._is_modified = False

        theme_type, _ = first_item.data(Qt.ItemDataRole.UserRole)
        assert theme_type == "builtin"

        with patch.object(QMessageBox, 'information') as mock_info:
            theme_widget._on_save_theme()
            mock_info.assert_called_once()


class TestApplyThemeWithUnsavedChanges:
    """Tests for lines 420-430: _on_apply_theme with unsaved changes."""

    def test_apply_with_unsaved_save(self, theme_widget, theme_manager):
        """Apply with unsaved changes, user chooses Save (line 427-428)."""
        # Create and select a custom theme
        theme_widget._on_new_theme()
        theme_widget._is_modified = True

        with patch.object(QMessageBox, 'question', return_value=QMessageBox.StandardButton.Save):
            with patch.object(theme_widget, '_on_save_theme') as mock_save:
                theme_widget._on_apply_theme()
                mock_save.assert_called_once()

        # Clean up
        for name in list(theme_manager.get_custom_theme_names()):
            if name.startswith("Custom Theme"):
                theme_manager.delete_custom_theme(name)

    def test_apply_with_unsaved_cancel(self, theme_widget):
        """Apply with unsaved changes, user chooses Cancel (line 429-430)."""
        theme_widget._is_modified = True
        signals = []
        theme_widget.theme_applied.connect(lambda n: signals.append(n))

        with patch.object(QMessageBox, 'question', return_value=QMessageBox.StandardButton.Cancel):
            theme_widget._on_apply_theme()

        # theme_applied should NOT have been emitted
        assert len(signals) == 0

    def test_apply_with_unsaved_no(self, theme_widget):
        """Apply with unsaved changes, user chooses No (line 420-430)."""
        # Select a theme first
        first_item = theme_widget._theme_list.item(0)
        theme_widget._theme_list.setCurrentItem(first_item)
        theme_widget._is_modified = True

        signals = []
        theme_widget.theme_applied.connect(lambda n: signals.append(n))

        with patch.object(QMessageBox, 'question', return_value=QMessageBox.StandardButton.No):
            theme_widget._on_apply_theme()

        # Should have applied without saving
        assert len(signals) == 1

    def test_apply_no_current_item(self, theme_widget):
        """Apply returns early when no current item selected (lines 432-434)."""
        theme_widget._is_modified = False
        theme_widget._theme_list.clearSelection()
        theme_widget._theme_list.setCurrentItem(None)

        signals = []
        theme_widget.theme_applied.connect(lambda n: signals.append(n))
        theme_widget._on_apply_theme()

        assert len(signals) == 0


class TestSettingsDialogThemeApplied:
    """Tests for line 605: SettingsDialog._on_theme_applied emits theme_changed."""

    def test_on_theme_applied_emits_signal(self, qapp, theme_manager):
        """_on_theme_applied emits theme_changed signal (line 605)."""
        dialog = SettingsDialog(theme_manager)
        signals = []
        dialog.theme_changed.connect(lambda name: signals.append(name))

        dialog._on_theme_applied("Dark")

        assert signals == ["Dark"]
        dialog.deleteLater()
        qapp.processEvents()
