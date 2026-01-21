"""
Font Toolbar Module

A floating mini toolbar that appears near selected text for quick font editing.
Similar to Microsoft Word's selection popup.
"""

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QFontComboBox, QSpinBox, QFrame
)
from PySide6.QtCore import Qt, Signal, QTimer, QPoint, QEvent
from PySide6.QtGui import QFont, QTextCharFormat, QTextCursor


class FontMiniToolbar(QFrame):
    """A floating toolbar for quick font editing of selected text."""
    
    font_changed = Signal(QFont)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._editor = None
        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self._check_hide)
        self._is_applying = False
        self._main_window = None
        
        self._setup_ui()
        self.hide()
    
    def set_main_window(self, main_window):
        """Set the main window to use as parent for positioning."""
        self._main_window = main_window
        self.setParent(main_window)
        self.raise_()
    
    def _setup_ui(self):
        """Initialize the toolbar UI."""
        
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Raised)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(4)
        
        self._font_combo = QFontComboBox()
        self._font_combo.setMaximumWidth(140)
        self._font_combo.currentFontChanged.connect(self._on_font_changed)
        layout.addWidget(self._font_combo)
        
        self._size_spin = QSpinBox()
        self._size_spin.setRange(6, 72)
        self._size_spin.setValue(12)
        self._size_spin.setMinimumWidth(50)
        self._size_spin.setMaximumWidth(60)
        self._size_spin.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self._size_spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._size_spin.editingFinished.connect(self._on_size_changed)
        self._size_spin.installEventFilter(self)
        layout.addWidget(self._size_spin)
        
        self._font_combo.installEventFilter(self)
        
        self.setFixedHeight(32)
    
    def set_theme_colors(self, bg_color: str, text_color: str, border_color: str):
        """Apply theme colors to the toolbar."""
        self.setStyleSheet(f"""
            FontMiniToolbar {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 4px;
            }}
            QFontComboBox {{
                background-color: {bg_color};
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 2px;
                padding: 2px 20px 2px 4px;
            }}
            QFontComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: center right;
                width: 16px;
                border: none;
                background: transparent;
            }}
            QFontComboBox::down-arrow {{
                width: 0;
                height: 0;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid {text_color};
            }}
            QFontComboBox:on {{
                border-bottom-left-radius: 0;
                border-bottom-right-radius: 0;
            }}
            QFontComboBox QAbstractItemView {{
                background-color: {bg_color};
                color: {text_color};
                border: 1px solid {border_color};
                selection-background-color: {border_color};
                selection-color: {text_color};
            }}
            QSpinBox {{
                background-color: {bg_color};
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 2px;
                padding: 2px 4px;
            }}
        """)
    
    def attach_to_editor(self, editor):
        """Attach the toolbar to an editor widget."""
        if self._editor:
            try:
                self._editor.selectionChanged.disconnect(self._on_selection_changed)
            except RuntimeError:
                pass
        
        self._editor = editor
        if editor:
            editor.selectionChanged.connect(self._on_selection_changed)
    
    def _on_selection_changed(self):
        """Handle selection changes in the editor."""
        if self._is_applying:
            return
            
        if not self._editor:
            self.hide()
            return
        
        cursor = self._editor.textCursor()
        if cursor.hasSelection():
            self._update_from_selection(cursor)
            self._position_near_selection(cursor)
            self.show()
            self._hide_timer.stop()
        else:
            self._hide_timer.start(300)
    
    def _check_hide(self):
        """Check if we should hide the toolbar."""
        if self._editor:
            cursor = self._editor.textCursor()
            if not cursor.hasSelection():
                self.hide()
    
    def _update_from_selection(self, cursor: QTextCursor):
        """Update toolbar controls from the selected text's format."""
        self._is_applying = True
        try:
            char_format = cursor.charFormat()
            font = char_format.font()
            
            if font.family():
                self._font_combo.setCurrentFont(font)
            
            size = font.pointSize()
            if size > 0:
                self._size_spin.setValue(size)
        finally:
            self._is_applying = False
    
    def _position_near_selection(self, cursor: QTextCursor):
        """Position the toolbar below the selection."""
        if not self._editor or not self._main_window:
            return
        
        cursor_rect = self._editor.cursorRect(cursor)
        
        viewport = self._editor.viewport()
        global_pos = viewport.mapToGlobal(cursor_rect.bottomLeft())
        
        local_pos = self._main_window.mapFromGlobal(global_pos)
        
        toolbar_x = local_pos.x()
        toolbar_y = local_pos.y() + 5
        
        main_rect = self._main_window.rect()
        
        if toolbar_y + self.height() > main_rect.bottom():
            top_global = viewport.mapToGlobal(cursor_rect.topLeft())
            top_local = self._main_window.mapFromGlobal(top_global)
            toolbar_y = top_local.y() - self.height() - 5
        
        if toolbar_x + self.width() > main_rect.right():
            toolbar_x = main_rect.right() - self.width() - 10
        
        if toolbar_x < main_rect.left():
            toolbar_x = main_rect.left() + 10
        
        self.move(toolbar_x, toolbar_y)
        self.raise_()
    
    def _on_font_changed(self, font: QFont):
        """Handle font family change."""
        if self._is_applying:
            return
        self._apply_font_to_selection()
    
    def _on_size_changed(self):
        """Handle font size change."""
        if self._is_applying:
            return
        self._apply_font_to_selection()
    
    def _apply_font_to_selection(self):
        """Apply the current font settings to the selection."""
        if not self._editor:
            return
        
        cursor = self._editor.textCursor()
        if not cursor.hasSelection():
            return
        
        self._is_applying = True
        try:
            font = self._font_combo.currentFont()
            font.setPointSize(self._size_spin.value())
            
            fmt = QTextCharFormat()
            fmt.setFont(font)
            cursor.mergeCharFormat(fmt)
            self._editor.setTextCursor(cursor)
            
            self.font_changed.emit(font)
        finally:
            self._is_applying = False
    
    def hideEvent(self, event):
        """Handle hide event."""
        super().hideEvent(event)
    
    def enterEvent(self, event):
        """Keep toolbar visible when mouse enters."""
        self._hide_timer.stop()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Start hide timer when mouse leaves."""
        if self._editor:
            cursor = self._editor.textCursor()
            if not cursor.hasSelection():
                self._hide_timer.start(300)
        super().leaveEvent(event)
    
    def eventFilter(self, obj, event):
        """Handle events for child widgets to manage focus."""
        if event.type() == QEvent.Type.MouseButtonPress:
            if obj in (self._size_spin, self._font_combo):
                self.activateWindow()
                obj.setFocus(Qt.FocusReason.MouseFocusReason)
                return False
        return super().eventFilter(obj, event)
