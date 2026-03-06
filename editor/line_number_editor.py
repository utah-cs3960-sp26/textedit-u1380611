"""
Line Number Editor Module

A QPlainTextEdit with a line number gutter, similar to VS Code.
"""

from PySide6.QtWidgets import QPlainTextEdit, QWidget, QTextEdit, QScrollBar, QStyleOptionSlider, QStyle
from PySide6.QtCore import Qt, QRect, QSize
from PySide6.QtGui import QPainter, QColor, QTextFormat, QTextCursor, QMouseEvent


class LineNumberArea(QWidget):
    """Widget that displays line numbers in the gutter."""
    
    def __init__(self, editor: "LineNumberedEditor"):
        super().__init__(editor)
        self._editor = editor
    
    def sizeHint(self) -> QSize:
        return QSize(self._editor.line_number_area_width(), 0)
    
    def paintEvent(self, event):
        self._editor.line_number_area_paint_event(event)


class JumpScrollBar(QScrollBar):
    """Scrollbar that jumps to the clicked position instead of paging."""

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            opt = QStyleOptionSlider()
            self.initStyleOption(opt)
            groove = self.style().subControlRect(
                QStyle.ComplexControl.CC_ScrollBar, opt,
                QStyle.SubControl.SC_ScrollBarGroove, self,
            )
            if groove.isValid():
                if self.orientation() == Qt.Orientation.Vertical:
                    pos = event.position().y()
                    total = groove.height()
                else:
                    pos = event.position().x()
                    total = groove.width()
                ratio = (pos - groove.top()) / total if self.orientation() == Qt.Orientation.Vertical else (pos - groove.left()) / total
                value = int(self.minimum() + ratio * (self.maximum() - self.minimum()))
                self.setValue(value)
                event.accept()
                return
        super().mousePressEvent(event)


class LineNumberedEditor(QPlainTextEdit):
    """QPlainTextEdit with line numbers displayed in a left margin."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setVerticalScrollBar(JumpScrollBar(Qt.Orientation.Vertical, self))
        
        self._line_number_area = LineNumberArea(self)
        
        self._bg_color = QColor("#1a1a1a")
        self._text_color = QColor("#6e7681")
        self._current_line_color = QColor("#c9d1d9")
        self._current_line_bg = QColor("#21262d")
        
        # Virtualisation support: offset added to block numbers for gutter display
        self._line_number_base: int = 0
        self._line_number_total: int | None = None
        # Wheel-event callback for virtualised scrolling
        self._virtual_wheel_handler = None
        
        # Unified extra-selection ownership: current-line + search highlights
        self._current_line_selection: QTextEdit.ExtraSelection | None = None
        self._search_selections: list = []
        self._last_current_block: int = -1
        self._cached_gutter_width: int = 40
        
        self.blockCountChanged.connect(self._update_line_number_area_width)
        self.updateRequest.connect(self._update_line_number_area)
        self.cursorPositionChanged.connect(self._highlight_current_line)
        
        self._update_line_number_area_width(0)
        self._highlight_current_line()
    
    def set_line_number_colors(self, bg: str, text: str, current_line: str, current_line_bg: str):
        """Set the colors for the line number area."""
        self._bg_color = QColor(bg)
        self._text_color = QColor(text)
        self._current_line_color = QColor(current_line)
        self._current_line_bg = QColor(current_line_bg)
        self._line_number_area.update()
        self._highlight_current_line()
    
    def set_line_number_context(self, base_line0: int, total_lines: int | None):
        """Set virtualisation context for the gutter.

        Args:
            base_line0: global 0-based line number of the first block.
            total_lines: total lines in the full document (for gutter width).
                         Pass ``None`` to revert to normal mode.
        """
        self._line_number_base = base_line0
        self._line_number_total = total_lines
        self._update_line_number_area_width(0)
        self._line_number_area.update()
    
    def line_number_area_width(self) -> int:
        """Return cached gutter width (recomputed on block-count or context change)."""
        return self._cached_gutter_width

    def _recompute_gutter_width(self):
        """Recompute and cache the gutter width."""
        digits = 1
        max_num = max(1, self._line_number_total or self.blockCount())
        while max_num >= 10:
            max_num //= 10
            digits += 1
        self._cached_gutter_width = 3 + self.fontMetrics().horizontalAdvance('9') * max(digits, 3) + 12

    def _update_line_number_area_width(self, _):
        """Update the viewport margins to accommodate line numbers."""
        self._recompute_gutter_width()
        self.setViewportMargins(self._cached_gutter_width, 0, 0, 0)
    
    def _update_line_number_area(self, rect: QRect, dy: int):
        """Update the line number area when scrolling or text changes."""
        if dy:
            self._line_number_area.scroll(0, dy)
        else:
            self._line_number_area.update(0, rect.y(), self._line_number_area.width(), rect.height())
    
    def resizeEvent(self, event):
        """Handle resize to adjust line number area."""
        super().resizeEvent(event)
        
        cr = self.contentsRect()
        self._line_number_area.setGeometry(
            QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height())
        )
    
    def set_search_selections(self, selections: list):
        """Set search-highlight extra selections (owned by find dialog)."""
        self._search_selections = selections
        self._apply_extra_selections()

    def clear_search_selections(self):
        """Remove all search-highlight extra selections."""
        self._search_selections = []
        self._apply_extra_selections()

    def _highlight_current_line(self):
        """Highlight the current line (skip if only column changed)."""
        block = self.textCursor().blockNumber()
        if block == self._last_current_block:
            return
        self._last_current_block = block

        self._current_line_selection = None
        if not self.isReadOnly():
            sel = QTextEdit.ExtraSelection()
            sel.format.setBackground(self._current_line_bg)
            sel.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            cursor = self.textCursor()
            cursor.clearSelection()
            sel.cursor = cursor
            self._current_line_selection = sel

        self._apply_extra_selections()

    def _apply_extra_selections(self):
        """Combine current-line and search selections into one setExtraSelections call."""
        selections = []
        if self._current_line_selection is not None:
            selections.append(self._current_line_selection)
        selections.extend(self._search_selections)
        super().setExtraSelections(selections)
    
    def line_number_area_paint_event(self, event):
        """Paint the line numbers."""
        painter = QPainter(self._line_number_area)
        painter.fillRect(event.rect(), self._bg_color)
        
        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())
        
        current_block = self.textCursor().blockNumber()
        base = self._line_number_base
        
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(base + block_number + 1)
                
                if block_number == current_block:
                    painter.setPen(self._current_line_color)
                else:
                    painter.setPen(self._text_color)
                
                painter.drawText(
                    0, top,
                    self._line_number_area.width() - 8, 
                    self.fontMetrics().height(),
                    Qt.AlignmentFlag.AlignRight, 
                    number
                )
            
            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            block_number += 1
    
    def wheelEvent(self, event):
        """Route wheel events through the virtual controller when active."""
        if self._virtual_wheel_handler is not None:
            self._virtual_wheel_handler(event)
            event.accept()
        else:
            super().wheelEvent(event)
