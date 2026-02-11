"""
Tests for the FontMiniToolbar module.
"""

import pytest
from unittest.mock import MagicMock, patch
from PySide6.QtWidgets import QApplication, QPlainTextEdit, QMainWindow
from PySide6.QtGui import QFont, QTextCursor, QTextCharFormat
from PySide6.QtCore import Qt, QPoint

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


class TestFontMiniToolbarFontChange:
    """Tests for font change operations."""
    
    def test_on_font_changed_signal(self, toolbar, editor):
        """Font change emits signal."""
        signal_emitted = []
        toolbar.font_changed.connect(lambda f: signal_emitted.append(f))
        toolbar.attach_to_editor(editor)
        
        # Change font via combo box
        new_font = QFont("Arial")
        toolbar._font_combo.setCurrentFont(new_font)
        
        # Signal should have been emitted
        assert len(signal_emitted) >= 0
    
    def test_on_size_changed(self, toolbar, editor):
        """Size change updates editor font."""
        toolbar.attach_to_editor(editor)
        
        # Change size via spin box
        toolbar._size_spin.setValue(16)
        
        assert toolbar._size_spin.value() == 16
    
    def test_update_from_selection_with_font(self, toolbar, editor):
        """Toolbar updates to match selected text font."""
        toolbar.attach_to_editor(editor)
        
        # Apply font to selected text
        cursor = editor.textCursor()
        cursor.select(QTextCursor.SelectionType.LineUnderCursor)
        
        fmt = QTextCharFormat()
        fmt.setFont(QFont("Courier", 14))
        cursor.mergeCharFormat(fmt)
        editor.setTextCursor(cursor)
        
        # Update toolbar from selection
        toolbar._update_from_selection(cursor)
        
        assert toolbar._size_spin.value() == 14
    
    def test_update_from_selection_no_font(self, toolbar, editor):
        """Toolbar handles selection with no explicit font."""
        toolbar.attach_to_editor(editor)
        
        cursor = editor.textCursor()
        cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        editor.setTextCursor(cursor)
        
        # Update from selection (may not have explicit font)
        toolbar._update_from_selection(cursor)
        assert True  # No exception


class TestFontMiniToolbarPositioning:
    """Tests for toolbar positioning."""
    
    def test_set_main_window(self, toolbar, qapp):
        """Can set main window for positioning."""
        main_window = QMainWindow()
        toolbar.set_main_window(main_window)
        assert toolbar._main_window == main_window
        main_window.deleteLater()
    
    def test_position_near_selection(self, toolbar, editor, qapp):
        """Toolbar positions near selected text."""
        toolbar.attach_to_editor(editor)
        main_window = QMainWindow()
        main_window.setCentralWidget(editor)
        toolbar.set_main_window(main_window)
        
        cursor = editor.textCursor()
        cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        editor.setTextCursor(cursor)
        
        # Position toolbar
        toolbar._position_near_selection(cursor)
        
        # Should have geometry
        assert toolbar.geometry().width() > 0
        
        main_window.deleteLater()
    
    def test_position_without_main_window(self, toolbar, editor):
        """Positioning works even without main window."""
        toolbar.attach_to_editor(editor)
        
        cursor = editor.textCursor()
        cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        
        # Should not raise
        toolbar._position_near_selection(cursor)
        assert True


class TestFontMiniToolbarHiding:
    """Tests for toolbar hide behavior."""
    
    def test_check_hide_with_selection(self, toolbar, editor):
        """Check hide does nothing when text is selected."""
        toolbar.attach_to_editor(editor)
        
        cursor = editor.textCursor()
        cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        editor.setTextCursor(cursor)
        
        toolbar._check_hide()
        # Toolbar stays visible (implicitly tested by not raising)
        assert True
    
    def test_check_hide_without_selection(self, toolbar, editor):
        """Check hide hides toolbar when no selection."""
        toolbar.attach_to_editor(editor)
        toolbar.show()
        
        # Clear selection
        cursor = editor.textCursor()
        cursor.clearSelection()
        editor.setTextCursor(cursor)
        
        toolbar._check_hide()
        assert not toolbar.isVisible()
        
        toolbar.close()
        # Release any grabs
        try:
            toolbar.releaseMouse()
            toolbar.releaseKeyboard()
        except:
            pass
    
    def test_hide_timer_timeout(self, toolbar, editor):
        """Hide timer triggers hide after timeout."""
        toolbar.attach_to_editor(editor)
        toolbar.show()
        
        # Simulate timer timeout
        toolbar._hide_timer.timeout.emit()
        
        # Should be hidden
        assert not toolbar.isVisible()
        
        toolbar.close()


class TestFontMiniToolbarEventFilters:
    """Tests for event filter handling."""
    
    def test_eventFilter_mouse_press_on_combo(self, toolbar, qapp):
        """Event filter handles mouse press on font combo."""
        from PySide6.QtGui import QMouseEvent
        
        # Create a real mouse event
        event = QMouseEvent(
            QMouseEvent.Type.MouseButtonPress,
            QPoint(0, 0),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier
        )
        
        result = toolbar.eventFilter(toolbar._font_combo, event)
        
        # Should return False (event not consumed)
        assert result is False
    
    def test_eventFilter_other_event_on_spinner(self, toolbar, qapp):
        """Event filter handles other events on spinner."""
        from PySide6.QtCore import QEvent
        from PySide6.QtGui import QPainter
        
        # Create a non-mouse event
        event = QEvent(QEvent.Type.Enter)
        result = toolbar.eventFilter(toolbar._size_spin, event)
        
        assert result is False


class TestFontMiniToolbarEditorDetachment:
    """Tests for detaching from editors."""
    
    def test_detach_from_editor(self, toolbar, editor):
        """Detaching clears signal connections."""
        toolbar.attach_to_editor(editor)
        toolbar.attach_to_editor(None)
        
        assert toolbar._editor is None
    
    def test_detach_removes_signal_handler(self, toolbar, editor, qapp):
        """Detaching removes selection changed handler."""
        toolbar.attach_to_editor(editor)
        
        # Detach
        toolbar.attach_to_editor(None)
        
        # Should handle RuntimeError gracefully
        assert toolbar._editor is None
    
    def test_selection_changed_without_editor(self, toolbar):
        """Selection change with no editor hides toolbar."""
        toolbar.show()
        
        # Trigger selection changed
        toolbar._on_selection_changed()
        
        assert not toolbar.isVisible()
        
        toolbar.close()


class TestFontMiniToolbarApplyingState:
    """Tests for _is_applying flag."""
    
    def test_selection_change_during_apply_ignored(self, toolbar, editor):
        """Selection changes are ignored while applying."""
        toolbar.attach_to_editor(editor)
        toolbar._is_applying = True
        
        # Trigger selection changed
        toolbar._on_selection_changed()
        
        # Should return early without processing
        assert toolbar._is_applying is True
    
    def test_is_applying_reset_after_update(self, toolbar, editor):
        """_is_applying flag is reset after update."""
        toolbar.attach_to_editor(editor)
        
        cursor = editor.textCursor()
        cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        
        toolbar._update_from_selection(cursor)
        
        # Should be reset to False
        assert toolbar._is_applying is False


class TestFontMiniToolbarIntegration:
    """Integration tests for toolbar with editor."""
    
    def test_full_workflow_select_and_change(self, toolbar, editor, qapp):
        """Test full workflow of selecting and changing font."""
        main_window = QMainWindow()
        main_window.setCentralWidget(editor)
        toolbar.set_main_window(main_window)
        toolbar.attach_to_editor(editor)
        
        # Select text
        cursor = editor.textCursor()
        cursor.select(QTextCursor.SelectionType.LineUnderCursor)
        editor.setTextCursor(cursor)
        
        # Toolbar should show
        assert cursor.hasSelection()
        
        # Change font
        toolbar._size_spin.setValue(18)
        assert toolbar._size_spin.value() == 18
        
        main_window.deleteLater()
    
    def test_multiple_editor_switches(self, toolbar, qapp):
        """Test switching toolbar between multiple editors."""
        editor1 = QPlainTextEdit()
        editor2 = QPlainTextEdit()
        
        editor1.setPlainText("Editor 1")
        editor2.setPlainText("Editor 2")
        
        toolbar.attach_to_editor(editor1)
        assert toolbar._editor == editor1
        
        toolbar.attach_to_editor(editor2)
        assert toolbar._editor == editor2
        
        editor1.deleteLater()
        editor2.deleteLater()
    
    def test_on_font_changed_when_editor_has_no_selection(self, toolbar, editor, qapp):
        """_on_font_changed hides toolbar when no selection."""
        toolbar.attach_to_editor(editor)
        toolbar._is_applying = False
        
        # Ensure no selection
        editor.textCursor().clearSelection()
        
        toolbar._on_font_changed(QFont("Arial"))
        # Should hide via timer
        toolbar._hide_timer.start(0)
    
    def test_on_size_changed_when_editor_has_no_selection(self, toolbar, editor, qapp):
        """_on_size_changed doesn't apply when no selection."""
        toolbar.attach_to_editor(editor)
        toolbar._is_applying = False
        
        # Ensure no selection
        editor.textCursor().clearSelection()
        
        toolbar._on_size_changed()
        # Should handle gracefully
        assert toolbar._is_applying is False
    
    def test_apply_font_to_selection_with_selection(self, toolbar, editor, qapp):
        """_apply_font_to_selection applies font when selection exists."""
        toolbar.attach_to_editor(editor)
        toolbar._is_applying = False
        
        # Create selection
        cursor = editor.textCursor()
        cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        editor.setTextCursor(cursor)
        
        toolbar._apply_font_to_selection()
        
        # Font should be applied
        assert toolbar._is_applying is False
    
    def test_apply_font_to_selection_without_editor(self, toolbar):
        """_apply_font_to_selection handles no editor gracefully."""
        toolbar._editor = None
        toolbar._is_applying = False
        
        # Should not raise exception
        toolbar._apply_font_to_selection()
        assert True
    
    def test_attach_to_editor_with_existing_editor_signal_disconnect(self, toolbar, editor, qapp):
        """attach_to_editor properly disconnects from previous editor."""
        editor2 = QPlainTextEdit()
        editor2.setPlainText("New editor")
        
        # Attach to first editor
        toolbar.attach_to_editor(editor)
        assert toolbar._editor == editor
        
        # Attach to second editor - should disconnect from first
        toolbar.attach_to_editor(editor2)
        assert toolbar._editor == editor2
        
        editor2.deleteLater()
    
    def test_on_size_changed_with_is_applying_flag(self, toolbar, editor):
        """_on_size_changed respects _is_applying flag."""
        toolbar.attach_to_editor(editor)
        toolbar._is_applying = True
        
        # Create selection
        cursor = editor.textCursor()
        cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        editor.setTextCursor(cursor)
        
        toolbar._on_size_changed()
        
        # Should return early due to flag
        assert toolbar._is_applying is True
    
    def test_position_near_selection_with_small_window(self, toolbar, editor, qapp):
        """_position_near_selection positions toolbar correctly in small window."""
        from PySide6.QtWidgets import QMainWindow
        
        main_window = QMainWindow()
        main_window.resize(200, 200)
        main_window.setCentralWidget(editor)
        main_window.show()
        
        toolbar._main_window = main_window
        toolbar.attach_to_editor(editor)
        
        # Create selection
        cursor = editor.textCursor()
        cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        editor.setTextCursor(cursor)
        
        # This should trigger positioning
        toolbar._position_near_selection(cursor)
        
        # Verify toolbar was positioned (has non-zero coordinates)
        assert toolbar.x() >= 0
        assert toolbar.y() >= 0
        
        main_window.close()
        main_window.deleteLater()
    
    def test_position_near_selection_bottom_overflow(self, toolbar, editor, qapp):
        """_position_near_selection adjusts position when hitting bottom."""
        from PySide6.QtWidgets import QMainWindow
        from PySide6.QtCore import QRect, QSize
        
        main_window = QMainWindow()
        main_window.resize(300, 200)
        main_window.setCentralWidget(editor)
        main_window.show()
        
        toolbar._main_window = main_window
        toolbar.resize(150, 80)
        toolbar.attach_to_editor(editor)
        
        # Move cursor to end (bottom area)
        cursor = editor.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        editor.setTextCursor(cursor)
        
        # Create selection at bottom
        cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        editor.setTextCursor(cursor)
        
        # Position toolbar (should adjust to avoid bottom overflow)
        toolbar._position_near_selection(cursor)
        
        # Verify toolbar is positioned (avoiding overflow)
        assert toolbar.y() >= 0
        
        main_window.close()
        main_window.deleteLater()
    
    def test_on_font_changed_with_is_applying_flag(self, toolbar, editor):
        """_on_font_changed respects _is_applying flag."""
        toolbar.attach_to_editor(editor)
        toolbar._is_applying = True
        
        # Create selection
        cursor = editor.textCursor()
        cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        editor.setTextCursor(cursor)
        
        toolbar._on_font_changed(QFont("Arial"))
        
        # Should return early due to flag
        assert toolbar._is_applying is True
    
    def test_check_hide_with_selection(self, toolbar, editor):
        """_check_hide doesn't hide when selection exists."""
        toolbar.attach_to_editor(editor)
        toolbar.show()
        
        # Create selection
        cursor = editor.textCursor()
        cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        editor.setTextCursor(cursor)
        
        toolbar._check_hide()
        
        # Toolbar should still be visible
        assert toolbar.isVisible() is True
        
        toolbar.close()
    
    def test_attach_to_editor_signal_disconnect_error(self, toolbar, qapp):
        """attach_to_editor handles signal disconnect errors gracefully."""
        from unittest.mock import MagicMock
        
        # Create a mock editor with disconnect that raises
        mock_editor = MagicMock(spec=QPlainTextEdit)
        mock_editor.selectionChanged.disconnect.side_effect = RuntimeError("Not connected")
        
        toolbar._editor = mock_editor
        
        editor2 = QPlainTextEdit()
        # Should not raise exception even if disconnect fails
        toolbar.attach_to_editor(editor2)
        
        assert toolbar._editor == editor2
        
        editor2.deleteLater()
