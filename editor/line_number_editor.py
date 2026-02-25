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
    
    def line_number_area_width(self) -> int:
        """Calculate the width needed for line numbers."""
        digits = 1
        max_num = max(1, self.blockCount())
        while max_num >= 10:
            max_num //= 10
            digits += 1
        
        space = 3 + self.fontMetrics().horizontalAdvance('9') * max(digits, 3) + 12
        return space
    
    def _update_line_number_area_width(self, _):
        """Update the viewport margins to accommodate line numbers."""
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)
    
    def _update_line_number_area(self, rect: QRect, dy: int):
        """Update the line number area when scrolling or text changes."""
        if dy:
            self._line_number_area.scroll(0, dy)
        else:
            self._line_number_area.update(0, rect.y(), self._line_number_area.width(), rect.height())
        
        if rect.contains(self.viewport().rect()):
            self._update_line_number_area_width(0)
    
    def resizeEvent(self, event):
        """Handle resize to adjust line number area."""
        super().resizeEvent(event)
        
        cr = self.contentsRect()
        self._line_number_area.setGeometry(
            QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height())
        )
    
    def _highlight_current_line(self):
        """Highlight the current line."""
        extra_selections = []
        
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            selection.format.setBackground(self._current_line_bg)
            selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            cursor = self.textCursor()
            cursor.clearSelection()
            selection.cursor = cursor
            extra_selections.append(selection)
        
        self.setExtraSelections(extra_selections)
    
    def line_number_area_paint_event(self, event):
        """Paint the line numbers."""
        painter = QPainter(self._line_number_area)
        painter.fillRect(event.rect(), self._bg_color)
        
        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())
        
        current_block = self.textCursor().blockNumber()
        
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                
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
