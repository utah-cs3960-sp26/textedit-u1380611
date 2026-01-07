"""
Split Container Module

Manages one or two editor panes in a horizontal split layout.
Handles drag-to-edge splitting and merging.
"""

from typing import Optional
from PySide6.QtWidgets import QWidget, QHBoxLayout, QSplitter, QRubberBand, QMessageBox
from PySide6.QtCore import Signal, Qt, QPoint, QRect, QSize

from editor.document import Document
from editor.editor_pane import EditorPane
from editor.tab_bar import EditorTabBar
from editor.file_handler import FileHandler


class SplitContainer(QWidget):
    """
    Container managing one or two horizontal editor panes.
    
    Handles:
    - Split creation via drag-to-edge
    - Split merging when a pane becomes empty
    - Tab transfers between panes
    """
    
    EDGE_THRESHOLD = 0.5  # 50% - left half creates left split, right half creates right split
    
    active_document_changed = Signal(object)
    document_modified = Signal(object, bool)
    layout_changed = Signal()
    split_swapped = Signal()
    close_app_requested = Signal()
    save_document_requested = Signal(object, int, object)  # document, tab_index, pane
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._panes: list[EditorPane] = []
        self._active_pane: Optional[EditorPane] = None
        self._dragging_tab_index: int = -1
        self._dragging_source_pane: Optional[EditorPane] = None
        self._file_handler = FileHandler()
        
        self._drop_indicator = QRubberBand(QRubberBand.Shape.Rectangle, self)
        
        self._setup_ui()
        self._create_initial_pane()
    
    def _setup_ui(self):
        """Initialize the layout."""
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        
        self._splitter = QSplitter(Qt.Orientation.Horizontal, self)
        self._layout.addWidget(self._splitter)
        
        self.setAcceptDrops(True)
    
    def _create_initial_pane(self):
        """Create the first editor pane with an empty document."""
        pane = self._create_pane()
        pane.add_new_document()
        self._active_pane = pane
    
    def _create_pane(self) -> EditorPane:
        """Create and configure a new editor pane."""
        pane = EditorPane(self)
        
        pane.document_changed.connect(self._on_document_changed)
        pane.document_modified.connect(self._on_document_modified)
        pane.pane_empty.connect(self._on_pane_empty)
        pane.tab_drag_started.connect(self._on_tab_drag_started)
        pane.close_tab_requested.connect(self._on_close_tab_requested)
        
        pane.tab_bar.dropEvent = lambda e: self._handle_tab_bar_drop(pane, e)
        
        self._panes.append(pane)
        self._splitter.addWidget(pane)
        
        return pane
    
    def _remove_pane(self, pane: EditorPane):
        """Remove a pane from the container."""
        if pane in self._panes:
            self._panes.remove(pane)
            pane.setParent(None)
            pane.deleteLater()
            
            if self._active_pane == pane and self._panes:
                self._active_pane = self._panes[0]
                self._active_pane.focus_editor()
            
            self.layout_changed.emit()
    
    @property
    def is_split(self) -> bool:
        """Check if the container is currently split."""
        return len(self._panes) > 1
    
    @property
    def active_pane(self) -> Optional[EditorPane]:
        """Get the currently active pane."""
        return self._active_pane
    
    @property
    def active_document(self) -> Optional[Document]:
        """Get the currently active document."""
        if self._active_pane:
            return self._active_pane.current_document
        return None
    
    @property
    def all_documents(self) -> list[Document]:
        """Get all documents from all panes."""
        docs = []
        for pane in self._panes:
            docs.extend(pane.documents)
        return docs
    
    def add_document(self, document: Document):
        """Add a document to the active pane."""
        if self._active_pane:
            self._active_pane.add_document(document)
    
    def add_new_document(self) -> Document:
        """Create and add a new document to the active pane."""
        if self._active_pane:
            return self._active_pane.add_new_document()
        return Document()
    
    def has_unsaved_changes(self) -> bool:
        """Check if any pane has unsaved changes."""
        return any(pane.has_unsaved_changes() for pane in self._panes)
    
    def set_word_wrap(self, enabled: bool):
        """Set word wrap on all panes."""
        for pane in self._panes:
            pane.set_word_wrap(enabled)
    
    def create_split(self, document: Document, edge: str) -> bool:
        """
        Create a split and move a document to the new pane.
        
        Args:
            document: Document to move to the new pane.
            edge: 'left' or 'right' indicating where to create the split.
            
        Returns:
            True if split was created, False otherwise.
        """
        if self.is_split:
            return False
        
        source_pane = self._get_pane_for_document(document)
        if source_pane is None:
            return False
        
        if source_pane.document_count <= 1:
            return False
        
        source_pane.sync_from_editor()
        source_pane.remove_document(document)
        
        new_pane = EditorPane(self)
        new_pane.document_changed.connect(self._on_document_changed)
        new_pane.document_modified.connect(self._on_document_modified)
        new_pane.pane_empty.connect(self._on_pane_empty)
        new_pane.tab_drag_started.connect(self._on_tab_drag_started)
        new_pane.close_tab_requested.connect(self._on_close_tab_requested)
        new_pane.tab_bar.dropEvent = lambda e: self._handle_tab_bar_drop(new_pane, e)
        
        if edge == "left":
            self._splitter.insertWidget(0, new_pane)
            self._panes.insert(0, new_pane)
        else:
            self._splitter.addWidget(new_pane)
            self._panes.append(new_pane)
        
        new_pane.add_document(document)
        self._active_pane = new_pane
        new_pane.focus_editor()
        
        sizes = [self.width() // 2, self.width() // 2]
        self._splitter.setSizes(sizes)
        
        self.layout_changed.emit()
        return True
    
    def merge_panes(self):
        """Merge split panes back into one."""
        if not self.is_split:
            return
        
        target_pane = self._panes[0]
        source_pane = self._panes[1]
        
        source_pane.sync_from_editor()
        
        for doc in source_pane.documents:
            target_pane.add_document(doc, activate=False)
        
        self._remove_pane(source_pane)
        self._active_pane = target_pane
        target_pane.focus_editor()
    
    def swap_panes(self):
        """Swap the left and right panes."""
        if not self.is_split:
            return
        
        self._panes[0].sync_from_editor()
        self._panes[1].sync_from_editor()
        
        left_pane = self._panes[0]
        right_pane = self._panes[1]
        
        self._splitter.insertWidget(0, right_pane)
        
        self._panes = [right_pane, left_pane]
        
        sizes = self._splitter.sizes()
        if len(sizes) == 2:
            self._splitter.setSizes([sizes[1], sizes[0]])
        
        self.split_swapped.emit()
        self.layout_changed.emit()
    
    def transfer_document(self, document: Document, source_pane: EditorPane, 
                          target_pane: EditorPane, insert_index: int = -1):
        """Transfer a document from one pane to another."""
        if source_pane == target_pane:
            return
        
        source_pane.sync_from_editor()
        
        will_be_empty = source_pane.document_count <= 1
        
        source_pane.remove_document(document)
        
        if insert_index >= 0:
            target_pane.insert_document(insert_index, document)
        else:
            target_pane.add_document(document)
        
        self._active_pane = target_pane
        target_pane.focus_editor()
    
    def _get_pane_for_document(self, document: Document) -> Optional[EditorPane]:
        """Find which pane contains a document."""
        for pane in self._panes:
            if document in pane.documents:
                return pane
        return None
    
    def get_pane_for_document(self, document: Document) -> Optional[EditorPane]:
        """Public method to find which pane contains a document."""
        return self._get_pane_for_document(document)
    
    def _on_document_changed(self, document: Document):
        """Handle document change in any pane."""
        for pane in self._panes:
            if document in pane.documents:
                self._active_pane = pane
                break
        self.active_document_changed.emit(document)
    
    def _on_document_modified(self, document: Document, modified: bool):
        """Handle document modification state change."""
        self.document_modified.emit(document, modified)
    
    def _on_pane_empty(self, pane: EditorPane):
        """Handle a pane becoming empty."""
        if len(self._panes) > 1:
            self._remove_pane(pane)
    
    def _on_close_tab_requested(self, pane: EditorPane, index: int):
        """Handle tab close request with save prompt."""
        doc = pane.get_document_at(index)
        if doc is None:
            return
        
        is_only_tab_in_only_pane = (pane.document_count <= 1 and len(self._panes) <= 1)
        if is_only_tab_in_only_pane:
            self.close_app_requested.emit()
            return
        
        if doc.is_modified:
            pane.sync_from_editor()
            
            result = QMessageBox.warning(
                self,
                "Unsaved Changes",
                f"Do you want to save changes to {doc.file_name}?",
                QMessageBox.StandardButton.Save |
                QMessageBox.StandardButton.Discard |
                QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Save
            )
            
            if result == QMessageBox.StandardButton.Cancel:
                return
            elif result == QMessageBox.StandardButton.Save:
                if doc.file_path:
                    save_result = self._file_handler.write_file(doc.file_path, doc.content)
                    if not save_result.success:
                        QMessageBox.critical(self, "Save Error", save_result.error_message)
                        return
                    doc.mark_saved()
                    pane.update_tab_title(doc)
                else:
                    self.save_document_requested.emit(doc, index, pane)
                    return
        
        pane.remove_document_at(index)
    
    def _on_tab_drag_started(self, tab_index: int, source_pane: EditorPane):
        """Track the tab being dragged for edge detection."""
        self._dragging_tab_index = tab_index
        self._dragging_source_pane = source_pane
    
    def _handle_tab_bar_drop(self, target_pane: EditorPane, event):
        """Handle tab dropped on a pane's tab bar."""
        if not event.mimeData().hasFormat(EditorTabBar.MIME_TYPE):
            event.ignore()
            return
        
        source_bar = event.source()
        if not isinstance(source_bar, EditorTabBar):
            event.ignore()
            return
        
        source_pane = None
        for pane in self._panes:
            if pane.tab_bar is source_bar:
                source_pane = pane
                break
        
        if source_pane is None or source_pane is target_pane:
            event.ignore()
            return
        
        tab_index = int(event.mimeData().data(EditorTabBar.MIME_TYPE).data().decode())
        document = source_pane.get_document_at(tab_index)
        
        if document is None:
            event.ignore()
            return
        
        drop_index = target_pane.tab_bar.get_drop_index(event.position().toPoint())
        self.transfer_document(document, source_pane, target_pane, drop_index)
        event.acceptProposedAction()
    
    def dragEnterEvent(self, event):
        """Accept tab drags for edge detection."""
        if event.mimeData().hasFormat(EditorTabBar.MIME_TYPE):
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dragMoveEvent(self, event):
        """Show drop indicator at edges."""
        if not event.mimeData().hasFormat(EditorTabBar.MIME_TYPE):
            event.ignore()
            return
        
        event.acceptProposedAction()
        
        pos = event.position().toPoint()
        edge = self._get_edge(pos)
        
        if edge and not self.is_split and self._dragging_source_pane:
            if self._dragging_source_pane.document_count > 1:
                half_width = self.width() // 2
                if edge == "left":
                    self._drop_indicator.setGeometry(0, 0, half_width, self.height())
                else:
                    self._drop_indicator.setGeometry(half_width, 0, half_width, self.height())
                self._drop_indicator.show()
                return
        
        self._drop_indicator.hide()
    
    def dragLeaveEvent(self, event):
        """Hide drop indicator when drag leaves."""
        self._drop_indicator.hide()
    
    def dropEvent(self, event):
        """Handle drop for split creation."""
        self._drop_indicator.hide()
        
        if not event.mimeData().hasFormat(EditorTabBar.MIME_TYPE):
            event.ignore()
            return
        
        if self._dragging_source_pane is None or self._dragging_tab_index < 0:
            event.ignore()
            return
        
        document = self._dragging_source_pane.get_document_at(self._dragging_tab_index)
        if document is None:
            event.ignore()
            return
        
        pos = event.position().toPoint()
        edge = self._get_edge(pos)
        
        if edge and not self.is_split:
            if self._dragging_source_pane.document_count > 1:
                if self.create_split(document, edge):
                    event.acceptProposedAction()
                    self._reset_drag_state()
                    return
        
        event.ignore()
        self._reset_drag_state()
    
    def _reset_drag_state(self):
        """Reset drag tracking state."""
        self._dragging_tab_index = -1
        self._dragging_source_pane = None
    
    def _get_edge(self, pos: QPoint) -> Optional[str]:
        """Determine if position is in left or right half."""
        mid = self.width() / 2
        if pos.x() < mid:
            return "left"
        else:
            return "right"
