"""
Main Window Module

Implements the main application window with menus, status bar, and split container.
"""

from typing import Optional
from PySide6.QtWidgets import (
    QMainWindow, QMenuBar, QStatusBar, QMessageBox,
    QFileDialog, QLabel
)
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtCore import Qt

from editor.document import Document
from editor.split_container import SplitContainer
from editor.file_handler import FileHandler


class MainWindow(QMainWindow):
    """Main application window with tabbed editor and split support."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._file_handler = FileHandler()
        self._word_wrap_enabled = True
        
        self._setup_ui()
        self._setup_menus()
        self._setup_status_bar()
        self._connect_signals()
        self._update_window_title()
        self._update_status_bar()
    
    def _setup_ui(self):
        """Initialize the main UI components."""
        self.setWindowTitle("TextEdit")
        self.setMinimumSize(800, 600)
        
        self._split_container = SplitContainer(self)
        self.setCentralWidget(self._split_container)
    
    def _setup_menus(self):
        """Create the menu bar and all menus."""
        menubar = self.menuBar()
        
        self._setup_file_menu(menubar)
        self._setup_edit_menu(menubar)
        self._setup_view_menu(menubar)
        self._setup_help_menu(menubar)
    
    def _setup_file_menu(self, menubar: QMenuBar):
        """Create the File menu."""
        file_menu = menubar.addMenu("&File")
        
        new_action = QAction("&New", self)
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.triggered.connect(self._on_new)
        file_menu.addAction(new_action)
        
        open_action = QAction("&Open...", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self._on_open)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        save_action = QAction("&Save", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self._on_save)
        file_menu.addAction(save_action)
        
        save_as_action = QAction("Save &As...", self)
        save_as_action.setShortcut(QKeySequence.StandardKey.SaveAs)
        save_as_action.triggered.connect(self._on_save_as)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        close_tab_action = QAction("&Close Tab", self)
        close_tab_action.setShortcut(QKeySequence("Ctrl+W"))
        close_tab_action.triggered.connect(self._on_close_tab)
        file_menu.addAction(close_tab_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
    
    def _setup_edit_menu(self, menubar: QMenuBar):
        """Create the Edit menu."""
        edit_menu = menubar.addMenu("&Edit")
        
        undo_action = QAction("&Undo", self)
        undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        undo_action.triggered.connect(self._on_undo)
        edit_menu.addAction(undo_action)
        
        redo_action = QAction("&Redo", self)
        redo_action.setShortcut(QKeySequence("Ctrl+Y"))
        redo_action.triggered.connect(self._on_redo)
        edit_menu.addAction(redo_action)
        
        edit_menu.addSeparator()
        
        cut_action = QAction("Cu&t", self)
        cut_action.setShortcut(QKeySequence.StandardKey.Cut)
        cut_action.triggered.connect(self._on_cut)
        edit_menu.addAction(cut_action)
        
        copy_action = QAction("&Copy", self)
        copy_action.setShortcut(QKeySequence.StandardKey.Copy)
        copy_action.triggered.connect(self._on_copy)
        edit_menu.addAction(copy_action)
        
        paste_action = QAction("&Paste", self)
        paste_action.setShortcut(QKeySequence.StandardKey.Paste)
        paste_action.triggered.connect(self._on_paste)
        edit_menu.addAction(paste_action)
        
        edit_menu.addSeparator()
        
        select_all_action = QAction("Select &All", self)
        select_all_action.setShortcut(QKeySequence.StandardKey.SelectAll)
        select_all_action.triggered.connect(self._on_select_all)
        edit_menu.addAction(select_all_action)
    
    def _setup_view_menu(self, menubar: QMenuBar):
        """Create the View menu."""
        view_menu = menubar.addMenu("&View")
        
        self._word_wrap_action = QAction("&Word Wrap", self)
        self._word_wrap_action.setCheckable(True)
        self._word_wrap_action.setChecked(self._word_wrap_enabled)
        self._word_wrap_action.triggered.connect(self._on_toggle_word_wrap)
        view_menu.addAction(self._word_wrap_action)
        
        self._status_bar_action = QAction("&Status Bar", self)
        self._status_bar_action.setCheckable(True)
        self._status_bar_action.setChecked(True)
        self._status_bar_action.triggered.connect(self._on_toggle_status_bar)
        view_menu.addAction(self._status_bar_action)
        
        view_menu.addSeparator()
        
        self._swap_panes_action = QAction("Swap Split &Panes", self)
        self._swap_panes_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
        self._swap_panes_action.triggered.connect(self._on_swap_panes)
        self._swap_panes_action.setEnabled(False)
        view_menu.addAction(self._swap_panes_action)
    
    def _setup_help_menu(self, menubar: QMenuBar):
        """Create the Help menu."""
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("&About", self)
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)
    
    def _setup_status_bar(self):
        """Create and configure the status bar."""
        self._status_bar = QStatusBar(self)
        self.setStatusBar(self._status_bar)
        
        self._file_label = QLabel("Untitled")
        self._position_label = QLabel("Ln 1, Col 1")
        self._modified_label = QLabel("")
        self._split_label = QLabel("")
        
        self._status_bar.addWidget(self._file_label, 1)
        self._status_bar.addPermanentWidget(self._split_label)
        self._status_bar.addPermanentWidget(self._modified_label)
        self._status_bar.addPermanentWidget(self._position_label)
    
    def _connect_signals(self):
        """Connect container signals."""
        self._split_container.active_document_changed.connect(self._on_document_changed)
        self._split_container.document_modified.connect(self._on_document_modified)
        self._split_container.layout_changed.connect(self._on_layout_changed)
        self._split_container.close_app_requested.connect(self.close)
        self._split_container.save_document_requested.connect(self._on_save_and_close_tab)
    
    def _get_active_editor(self):
        """Get the currently active editor widget."""
        pane = self._split_container.active_pane
        if pane:
            return pane.editor
        return None
    
    def _update_window_title(self):
        """Update the window title based on current state."""
        doc = self._split_container.active_document
        if doc:
            file_name = doc.file_name
            modified = "*" if doc.is_modified else ""
            self.setWindowTitle(f"{file_name}{modified} - TextEdit")
        else:
            self.setWindowTitle("TextEdit")
    
    def _update_status_bar(self):
        """Update all status bar elements."""
        doc = self._split_container.active_document
        
        if doc:
            self._file_label.setText(doc.file_name)
            self._modified_label.setText("Modified" if doc.is_modified else "")
        else:
            self._file_label.setText("Untitled")
            self._modified_label.setText("")
        
        editor = self._get_active_editor()
        if editor:
            cursor = editor.textCursor()
            line = cursor.blockNumber() + 1
            column = cursor.columnNumber() + 1
            self._position_label.setText(f"Ln {line}, Col {column}")
        
        if self._split_container.is_split:
            self._split_label.setText("Split View")
        else:
            self._split_label.setText("")
    
    def _on_document_changed(self, document: Document):
        """Handle active document change."""
        self._update_window_title()
        self._update_status_bar()
        
        editor = self._get_active_editor()
        if editor:
            editor.cursorPositionChanged.connect(self._on_cursor_position_changed)
    
    def _on_document_modified(self, document: Document, modified: bool):
        """Handle document modification state change."""
        self._update_window_title()
        self._update_status_bar()
    
    def _on_layout_changed(self):
        """Handle split layout changes."""
        self._update_status_bar()
        self._swap_panes_action.setEnabled(self._split_container.is_split)
    
    def _on_cursor_position_changed(self):
        """Handle cursor position changes."""
        editor = self._get_active_editor()
        if editor:
            cursor = editor.textCursor()
            line = cursor.blockNumber() + 1
            column = cursor.columnNumber() + 1
            self._position_label.setText(f"Ln {line}, Col {column}")
    
    def _prompt_save_changes(self, document: Document) -> bool:
        """
        Prompt user to save changes for a specific document.
        
        Returns:
            True if safe to proceed, False if operation should be cancelled.
        """
        if not document.is_modified:
            return True
        
        result = QMessageBox.warning(
            self,
            "Unsaved Changes",
            f"Do you want to save changes to {document.file_name}?",
            QMessageBox.StandardButton.Save |
            QMessageBox.StandardButton.Discard |
            QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Save
        )
        
        if result == QMessageBox.StandardButton.Save:
            if document.file_path:
                return self._save_document(document)
            else:
                return self._save_document_as(document)
        elif result == QMessageBox.StandardButton.Discard:
            return True
        else:
            return False
    
    def _prompt_save_all(self) -> bool:
        """Prompt to save all unsaved documents."""
        for doc in self._split_container.all_documents:
            if not self._prompt_save_changes(doc):
                return False
        return True
    
    def _on_new(self):
        """Handle File > New action."""
        self._split_container.add_new_document()
        self._update_window_title()
        self._update_status_bar()
    
    def _on_open(self):
        """Handle File > Open action."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open File",
            "",
            "Text Files (*.txt);;All Files (*)"
        )
        
        if not file_path:
            return
        
        result = self._file_handler.read_file(file_path)
        
        if result.success:
            doc = Document(content=result.content, file_path=file_path)
            
            current_doc = self._split_container.active_document
            pane = self._split_container.active_pane
            
            if (current_doc and pane and
                current_doc.file_path is None and
                not current_doc.is_modified and
                current_doc.content == ""):
                pane.remove_document(current_doc)
            
            self._split_container.add_document(doc)
            self._update_window_title()
            self._update_status_bar()
        else:
            self._show_error("Open Error", result.error_message)
    
    def _on_save(self) -> bool:
        """Handle File > Save action."""
        doc = self._split_container.active_document
        if doc is None:
            return False
        
        pane = self._split_container.active_pane
        if pane:
            pane._save_current_state()
        
        if doc.file_path:
            return self._save_document(doc)
        else:
            return self._on_save_as()
    
    def _on_save_as(self) -> bool:
        """Handle File > Save As action."""
        doc = self._split_container.active_document
        if doc is None:
            return False
        
        pane = self._split_container.active_pane
        if pane:
            pane._save_current_state()
        
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Save File",
            "",
            "Text Files (*.txt);;All Files (*)"
        )
        
        if not file_path:
            return False
        
        if selected_filter == "Text Files (*.txt)" and not file_path.endswith(".txt"):
            file_path += ".txt"
        
        return self._save_document(doc, file_path)
    
    def _save_document(self, document: Document, file_path: Optional[str] = None) -> bool:
        """Save a document to disk."""
        path = file_path or document.file_path
        if not path:
            return False
        
        result = self._file_handler.write_file(path, document.content)
        
        if result.success:
            document.mark_saved(path)
            pane = self._split_container.get_pane_for_document(document)
            if pane:
                pane.update_tab_title(document)
            self._update_window_title()
            self._update_status_bar()
            return True
        else:
            self._show_error("Save Error", result.error_message)
            return False
    
    def _save_document_as(self, document: Document) -> bool:
        """Save a document with a file dialog."""
        pane = self._split_container.get_pane_for_document(document)
        if pane:
            pane.sync_from_editor()
        
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Save File",
            document.file_name if document.file_name != "Untitled" else "",
            "Text Files (*.txt);;All Files (*)"
        )
        
        if not file_path:
            return False
        
        if selected_filter == "Text Files (*.txt)" and not file_path.endswith(".txt"):
            file_path += ".txt"
        
        return self._save_document(document, file_path)
    
    def _on_save_and_close_tab(self, document: Document, tab_index: int, pane):
        """Handle save request for untitled document before closing tab."""
        if self._save_document_as(document):
            pane.remove_document_at(tab_index)
    
    def _on_close_tab(self):
        """Handle Close Tab action."""
        pane = self._split_container.active_pane
        if pane is None:
            return
        
        if pane.document_count <= 1 and len(self._split_container._panes) <= 1:
            self.close()
            return
        
        doc = pane.current_document
        if doc is None:
            return
        
        pane.sync_from_editor()
        
        if doc.is_modified:
            if not self._prompt_save_changes(doc):
                return
        
        pane.remove_document(doc)
        
        self._update_window_title()
        self._update_status_bar()
    
    def _on_undo(self):
        """Handle Edit > Undo."""
        editor = self._get_active_editor()
        if editor:
            editor.undo()
    
    def _on_redo(self):
        """Handle Edit > Redo."""
        editor = self._get_active_editor()
        if editor:
            editor.redo()
    
    def _on_cut(self):
        """Handle Edit > Cut."""
        editor = self._get_active_editor()
        if editor:
            editor.cut()
    
    def _on_copy(self):
        """Handle Edit > Copy."""
        editor = self._get_active_editor()
        if editor:
            editor.copy()
    
    def _on_paste(self):
        """Handle Edit > Paste."""
        editor = self._get_active_editor()
        if editor:
            editor.paste()
    
    def _on_select_all(self):
        """Handle Edit > Select All."""
        editor = self._get_active_editor()
        if editor:
            editor.selectAll()
    
    def _on_toggle_word_wrap(self, checked: bool):
        """Handle View > Word Wrap toggle."""
        self._word_wrap_enabled = checked
        self._split_container.set_word_wrap(checked)
    
    def _on_toggle_status_bar(self, checked: bool):
        """Handle View > Status Bar toggle."""
        self._status_bar.setVisible(checked)
    
    def _on_swap_panes(self):
        """Handle View > Swap Split Panes."""
        self._split_container.swap_panes()
    
    def _on_about(self):
        """Handle Help > About action."""
        QMessageBox.about(
            self,
            "About TextEdit",
            "TextEdit\n\n"
            "A simple, cross-platform text editor with tabs and split view.\n\n"
            "Built with Python and Qt (PySide6)."
        )
    
    def _show_error(self, title: str, message: str):
        """Show an error dialog."""
        QMessageBox.critical(self, title, message)
    
    def closeEvent(self, event):
        """Handle window close event."""
        if self._prompt_save_all():
            event.accept()
        else:
            event.ignore()
