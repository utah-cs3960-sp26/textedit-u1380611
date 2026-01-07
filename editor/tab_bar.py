"""
Custom Tab Bar with Drag Support

Handles tab reordering and emits signals for split/merge operations.
"""

from PySide6.QtWidgets import QTabBar, QToolButton
from PySide6.QtCore import Signal, Qt, QPoint, QMimeData, QTimer
from PySide6.QtGui import QDrag, QMouseEvent, QDragEnterEvent, QDragMoveEvent, QDropEvent


class EditorTabBar(QTabBar):
    """
    Custom tab bar with drag-and-drop support for reordering and split/merge.
    
    Signals:
        new_tab_requested: Emitted when the "+" button is clicked
        tab_close_requested: Emitted when a tab close is requested
        external_drag_started: Emitted when tab is dragged outside the tab bar
    """
    
    new_tab_requested = Signal()
    tab_close_requested = Signal(int)
    external_drag_started = Signal(int, QPoint)
    
    MIME_TYPE = "application/x-textedit-tab"
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._drag_start_pos: QPoint | None = None
        self._drag_tab_index: int = -1
        
        self.setMovable(True)
        self.setTabsClosable(True)
        self.setAcceptDrops(True)
        self.setElideMode(Qt.TextElideMode.ElideRight)
        self.setExpanding(False)
        self.setDocumentMode(True)
        
        self.tabCloseRequested.connect(self._on_tab_close_requested)
        
        self._setup_new_tab_button()
    
    def _setup_new_tab_button(self):
        """Add a '+' button at the end of the tab bar."""
        self._new_tab_button = QToolButton(self)
        self._new_tab_button.setText("+")
        self._new_tab_button.setAutoRaise(True)
        self._new_tab_button.setFixedSize(24, 24)
        self._new_tab_button.clicked.connect(self.new_tab_requested.emit)
        self._position_new_tab_button()
    
    def _position_new_tab_button(self):
        """Position the '+' button after the last tab."""
        if self.count() == 0:
            x = 4
        else:
            last_tab_rect = self.tabRect(self.count() - 1)
            x = last_tab_rect.right() + 4
        
        y = (self.height() - self._new_tab_button.height()) // 2
        self._new_tab_button.move(x, max(0, y))
    
    def resizeEvent(self, event):
        """Handle resize to reposition the '+' button."""
        super().resizeEvent(event)
        self._position_new_tab_button()
    
    def tabInserted(self, index: int):
        """Handle tab insertion."""
        super().tabInserted(index)
        QTimer.singleShot(0, self._position_new_tab_button)
    
    def tabRemoved(self, index: int):
        """Handle tab removal."""
        super().tabRemoved(index)
        QTimer.singleShot(0, self._position_new_tab_button)
    
    def tabLayoutChange(self):
        """Handle tab layout changes."""
        super().tabLayoutChange()
        QTimer.singleShot(0, self._position_new_tab_button)
    
    def mousePressEvent(self, event: QMouseEvent):
        """Track drag start position."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_pos = event.pos()
            self._drag_tab_index = self.tabAt(event.pos())
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """Detect when drag leaves the tab bar vertically."""
        super().mouseMoveEvent(event)
        
        if self._drag_tab_index < 0 or self._drag_start_pos is None:
            return
        
        if not self.rect().contains(event.pos()):
            if event.pos().y() < 0 or event.pos().y() > self.height():
                self._start_external_drag(event)
    
    def _start_external_drag(self, event: QMouseEvent):
        """Start a drag operation for split/merge."""
        if self._drag_tab_index < 0:
            return
            
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setData(self.MIME_TYPE, str(self._drag_tab_index).encode())
        drag.setMimeData(mime_data)
        
        self.external_drag_started.emit(self._drag_tab_index, self.mapToGlobal(event.pos()))
        
        drag.exec(Qt.DropAction.MoveAction)
        
        self._drag_start_pos = None
        self._drag_tab_index = -1
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """Reset drag state on mouse release."""
        self._drag_start_pos = None
        self._drag_tab_index = -1
        super().mouseReleaseEvent(event)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Accept tab drags from other tab bars."""
        if event.mimeData().hasFormat(self.MIME_TYPE):
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dragMoveEvent(self, event: QDragMoveEvent):
        """Handle drag movement over this tab bar."""
        if event.mimeData().hasFormat(self.MIME_TYPE):
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dropEvent(self, event: QDropEvent):
        """Handle drop from another tab bar - emit signal for parent to handle."""
        if not event.mimeData().hasFormat(self.MIME_TYPE):
            event.ignore()
            return
        
        source_bar = event.source()
        if source_bar is self or not isinstance(source_bar, EditorTabBar):
            event.ignore()
            return
        
        event.acceptProposedAction()
    
    def get_drop_index(self, pos: QPoint) -> int:
        """Determine insertion index based on drop position."""
        for i in range(self.count()):
            rect = self.tabRect(i)
            if pos.x() < rect.center().x():
                return i
        return self.count()
    
    def _on_tab_close_requested(self, index: int):
        """Forward tab close request."""
        self.tab_close_requested.emit(index)
