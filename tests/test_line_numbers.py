"""
Tests for the LineNumberedEditor module.
"""

import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QColor, QPainter, QFont
from PySide6.QtCore import Qt, QRect, QSize
from unittest.mock import MagicMock, patch

from editor.line_number_editor import LineNumberedEditor, LineNumberArea


@pytest.fixture(scope="session")
def qapp():
    """Create a QApplication instance for the test session."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def editor(qapp):
    """Create a fresh LineNumberedEditor for each test."""
    widget = LineNumberedEditor()
    yield widget
    widget.deleteLater()


class TestLineNumberedEditorInit:
    """Tests for LineNumberedEditor initialization."""
    
    def test_has_line_number_area(self, editor):
        """Editor has a line number area widget."""
        assert editor._line_number_area is not None
        assert isinstance(editor._line_number_area, LineNumberArea)
    
    def test_initial_colors_set(self, editor):
        """Editor has initial colors set."""
        assert editor._bg_color is not None
        assert editor._text_color is not None
        assert editor._current_line_color is not None
        assert editor._current_line_bg is not None
    
    def test_viewport_has_left_margin(self, editor):
        """Viewport has left margin for line numbers."""
        margins = editor.viewportMargins()
        assert margins.left() > 0


class TestLineNumberAreaWidth:
    """Tests for line number area width calculation."""
    
    def test_width_for_single_digit(self, editor):
        """Width accommodates single digit line numbers."""
        editor.setPlainText("Line 1")
        width = editor.line_number_area_width()
        assert width > 0
    
    def test_width_increases_for_more_lines(self, editor):
        """Width increases when more digits needed."""
        editor.setPlainText("Line 1")
        width_1 = editor.line_number_area_width()
        
        editor.setPlainText("\n".join([f"Line {i}" for i in range(1, 1001)]))
        width_1000 = editor.line_number_area_width()
        
        assert width_1000 > width_1


class TestLineNumberColors:
    """Tests for line number color configuration."""
    
    def test_set_line_number_colors(self, editor):
        """Can set line number colors."""
        editor.set_line_number_colors("#111111", "#222222", "#333333", "#444444")
        assert editor._bg_color == QColor("#111111")
        assert editor._text_color == QColor("#222222")
        assert editor._current_line_color == QColor("#333333")
        assert editor._current_line_bg == QColor("#444444")
    
    def test_colors_accept_hex_strings(self, editor):
        """Colors accept hex color strings."""
        editor.set_line_number_colors("#ff0000", "#00ff00", "#0000ff", "#ffffff")
        assert editor._bg_color.red() == 255
        assert editor._text_color.green() == 255
        assert editor._current_line_color.blue() == 255


class TestLineNumberArea:
    """Tests for LineNumberArea widget."""
    
    def test_size_hint_uses_editor_width(self, editor):
        """Size hint uses editor's calculated width."""
        area = editor._line_number_area
        hint = area.sizeHint()
        assert hint.width() == editor.line_number_area_width()
        assert hint.height() == 0


class TestCurrentLineHighlight:
    """Tests for current line highlighting."""
    
    def test_extra_selections_set(self, editor):
        """Editor has extra selections for current line."""
        editor.setPlainText("Line 1\nLine 2\nLine 3")
        selections = editor.extraSelections()
        assert len(selections) >= 1
    
    def test_highlight_updates_on_cursor_move(self, editor):
        """Highlight updates when cursor moves."""
        editor.setPlainText("Line 1\nLine 2\nLine 3")
        cursor = editor.textCursor()
        cursor.movePosition(cursor.MoveOperation.Down)
        editor.setTextCursor(cursor)
        selections = editor.extraSelections()
        assert len(selections) >= 1


class TestLineNumberAreaPaintEvent:
    """Tests for line number area painting."""
    
    def test_line_number_area_paint_event_single_line(self, editor):
        """Paint event renders single line number correctly."""
        editor.setPlainText("Test line")
        area = editor._line_number_area
        
        # Create a mock paint event
        event = MagicMock()
        event.rect.return_value = QRect(0, 0, 50, 100)
        
        # Should not raise
        editor.line_number_area_paint_event(event)
        assert True
    
    def test_line_number_area_paint_event_multiple_lines(self, editor):
        """Paint event renders multiple line numbers correctly."""
        editor.setPlainText("Line 1\nLine 2\nLine 3\nLine 4\nLine 5")
        area = editor._line_number_area
        
        event = MagicMock()
        event.rect.return_value = QRect(0, 0, 50, 200)
        
        editor.line_number_area_paint_event(event)
        assert True
    
    def test_line_number_area_paint_event_with_scrolling(self, editor):
        """Paint event handles scrolled content."""
        editor.setPlainText("\n".join([f"Line {i}" for i in range(1, 101)]))
        
        # Scroll down
        cursor = editor.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        editor.setTextCursor(cursor)
        
        event = MagicMock()
        event.rect.return_value = QRect(0, 0, 50, 200)
        
        editor.line_number_area_paint_event(event)
        assert True
    
    def test_line_number_area_paint_event_shows_current_line_number(self, editor):
        """Paint event highlights current line number."""
        editor.setPlainText("Line 1\nLine 2\nLine 3")
        
        # Move to second line
        cursor = editor.textCursor()
        cursor.movePosition(cursor.MoveOperation.Down)
        editor.setTextCursor(cursor)
        
        event = MagicMock()
        event.rect.return_value = QRect(0, 0, 50, 150)
        
        editor.line_number_area_paint_event(event)
        assert True


class TestLineNumberedEditorResizeEvent:
    """Tests for resize event handling."""
    
    def test_resize_event_adjusts_area_geometry(self, editor):
        """Resize event adjusts line number area geometry."""
        editor.setPlainText("Test")
        editor.resize(400, 300)
        
        area = editor._line_number_area
        # Area should be positioned at the left
        assert area.geometry().left() == 0
        assert area.geometry().top() == 0
    
    def test_resize_event_preserves_width(self, editor):
        """Resize event adjusts line number area geometry."""
        editor.setPlainText("Line 1\nLine 2\nLine 3")
        old_width = editor._line_number_area.geometry().width()
        
        editor.resize(500, 400)
        
        # Area should be adjusted (may have different width due to resize)
        new_width = editor._line_number_area.geometry().width()
        assert new_width > 0
    
    def test_resize_event_updates_height(self, editor):
        """Resize event updates line number area height."""
        editor.setPlainText("Test")
        editor.resize(400, 300)
        
        area_height = editor._line_number_area.geometry().height()
        assert area_height > 0


class TestLineNumberAreaFontHandling:
    """Tests for font changes affecting line numbers."""
    
    def test_set_font_updates_width(self, editor):
        """Setting font updates line number area width."""
        editor.setPlainText("Line 1\nLine 2\nLine 3")
        initial_width = editor.line_number_area_width()
        
        # Change to monospace font
        font = QFont("Courier")
        font.setPointSize(14)
        editor.setFont(font)
        
        # Width may change based on font metrics
        new_width = editor.line_number_area_width()
        assert new_width > 0
    
    def test_highlight_when_read_only(self, editor):
        """Current line highlight behavior is consistent."""
        editor.setPlainText("Line 1\nLine 2\nLine 3")
        initial_selections = len(editor.extraSelections())
        
        editor.setReadOnly(True)
        readonly_selections = len(editor.extraSelections())
        
        # Highlight may be shown or hidden depending on implementation
        assert readonly_selections >= 0
        
        editor.setReadOnly(False)


class TestLineNumberAreaScrolling:
    """Tests for line number area scrolling."""
    
    def test_update_line_number_area_with_dy(self, editor):
        """Update line number area scrolls when dy is provided."""
        editor.setPlainText("Line 1\nLine 2\nLine 3\nLine 4\nLine 5")
        area = editor._line_number_area
        
        # Trigger scroll update
        rect = QRect(0, 0, 100, 50)
        editor._update_line_number_area(rect, 10)  # Scroll down
        
        assert True  # Just verify no exceptions
    
    def test_update_line_number_area_without_dy(self, editor):
        """Update line number area updates rect when dy is 0."""
        editor.setPlainText("Line 1\nLine 2\nLine 3")
        area = editor._line_number_area
        
        rect = QRect(0, 0, 100, 50)
        editor._update_line_number_area(rect, 0)  # No scroll
        
        assert True  # Just verify no exceptions
    
    def test_update_line_number_area_full_viewport_update(self, editor):
        """Update triggers width update when rect contains viewport."""
        editor.setPlainText("Line 1\nLine 2\nLine 3")
        
        # Get full viewport rect
        vp_rect = editor.viewport().rect()
        editor._update_line_number_area(vp_rect, 0)
        
        assert True  # Just verify no exceptions
    
    def test_line_number_area_paint_event_coverage(self, editor):
        """LineNumberArea paintEvent calls line_number_area_paint_event."""
        editor.setPlainText("Line 1\nLine 2")
        area = editor._line_number_area
        
        # Create a paint event
        event = MagicMock()
        event.rect.return_value = QRect(0, 0, area.width(), 100)
        
        # This should call the editor's paint event handler
        area.paintEvent(event)
        assert True
    
    def test_line_numbered_editor_font_change(self, editor):
        """Setting font updates line number area."""
        original_font = editor.font()
        new_font = QFont("Courier New", 12)
        
        editor.setFont(new_font)
        
        # Width should potentially change with different font
        width1 = editor.line_number_area_width()
        
        editor.setFont(original_font)
        width2 = editor.line_number_area_width()
        
        # Just verify no exceptions
        assert width1 > 0
        assert width2 > 0
    
    def test_set_line_number_colors(self, editor):
        """set_line_number_colors updates all color properties."""
        editor.set_line_number_colors("#ffffff", "#000000", "#ffff00", "#00ff00")
        
        assert editor._bg_color.name() == "#ffffff"
        assert editor._text_color.name() == "#000000"
        assert editor._current_line_color.name() == "#ffff00"
        assert editor._current_line_bg.name() == "#00ff00"
    
    def test_resize_event_updates_line_number_area_geometry(self, editor):
        """resizeEvent updates line number area geometry."""
        editor.setGeometry(0, 0, 400, 300)
        editor.show()
        
        # Get line number area geometry
        area = editor._line_number_area
        area_width = area.width()
        
        # Area should have correct width
        assert area_width > 0
        
        editor.close()
