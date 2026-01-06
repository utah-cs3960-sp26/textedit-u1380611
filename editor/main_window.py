"""
Main Window Module

Implements the main application window with menus and status bar.
"""

from typing import Optional
from PySide6.QtWidgets import (
    QMainWindow, QMenuBar, QMenu, QStatusBar, QMessageBox,
    QFileDialog, QLabel, QWidget, QVBoxLayout
)
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtCore import Qt

from editor.editor_widget import EditorWidget
from editor.file_handler import FileHandler, FileError


class MainWindow(QMainWindow):
    """Main application window with editor, menus, and status bar."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._file_handler = FileHandler()
        
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
        
        self._editor = EditorWidget(self)
        self.setCentralWidget(self._editor)
    
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
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
    
    def _setup_edit_menu(self, menubar: QMenuBar):
        """Create the Edit menu."""
        edit_menu = menubar.addMenu("&Edit")
        
        undo_action = QAction("&Undo", self)
        undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        undo_action.triggered.connect(self._editor.undo)
        edit_menu.addAction(undo_action)
        
        redo_action = QAction("&Redo", self)
        redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        redo_action.triggered.connect(self._editor.redo)
        edit_menu.addAction(redo_action)
        
        edit_menu.addSeparator()
        
        cut_action = QAction("Cu&t", self)
        cut_action.setShortcut(QKeySequence.StandardKey.Cut)
        cut_action.triggered.connect(self._editor.cut)
        edit_menu.addAction(cut_action)
        
        copy_action = QAction("&Copy", self)
        copy_action.setShortcut(QKeySequence.StandardKey.Copy)
        copy_action.triggered.connect(self._editor.copy)
        edit_menu.addAction(copy_action)
        
        paste_action = QAction("&Paste", self)
        paste_action.setShortcut(QKeySequence.StandardKey.Paste)
        paste_action.triggered.connect(self._editor.paste)
        edit_menu.addAction(paste_action)
        
        edit_menu.addSeparator()
        
        select_all_action = QAction("Select &All", self)
        select_all_action.setShortcut(QKeySequence.StandardKey.SelectAll)
        select_all_action.triggered.connect(self._editor.selectAll)
        edit_menu.addAction(select_all_action)
    
    def _setup_view_menu(self, menubar: QMenuBar):
        """Create the View menu."""
        view_menu = menubar.addMenu("&View")
        
        self._word_wrap_action = QAction("&Word Wrap", self)
        self._word_wrap_action.setCheckable(True)
        self._word_wrap_action.setChecked(self._editor.is_word_wrap_enabled())
        self._word_wrap_action.triggered.connect(self._on_toggle_word_wrap)
        view_menu.addAction(self._word_wrap_action)
        
        self._status_bar_action = QAction("&Status Bar", self)
        self._status_bar_action.setCheckable(True)
        self._status_bar_action.setChecked(True)
        self._status_bar_action.triggered.connect(self._on_toggle_status_bar)
        view_menu.addAction(self._status_bar_action)
    
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
        
        self._status_bar.addWidget(self._file_label, 1)
        self._status_bar.addPermanentWidget(self._modified_label)
        self._status_bar.addPermanentWidget(self._position_label)
    
    def _connect_signals(self):
        """Connect editor signals to status bar updates."""
        self._editor.cursor_position_changed.connect(self._on_cursor_position_changed)
        self._editor.modified_state_changed.connect(self._on_modified_state_changed)
    
    def _update_window_title(self):
        """Update the window title based on current state."""
        file_name = self._editor.file_name
        modified = "*" if self._editor.is_modified else ""
        self.setWindowTitle(f"{file_name}{modified} - TextEdit")
    
    def _update_status_bar(self):
        """Update all status bar elements."""
        self._file_label.setText(self._editor.file_name)
        
        line, column = self._editor.get_cursor_position()
        self._position_label.setText(f"Ln {line}, Col {column}")
        
        self._modified_label.setText("Modified" if self._editor.is_modified else "")
    
    def _on_cursor_position_changed(self, line: int, column: int):
        """Handle cursor position changes."""
        self._position_label.setText(f"Ln {line}, Col {column}")
    
    def _on_modified_state_changed(self, modified: bool):
        """Handle document modification state changes."""
        self._modified_label.setText("Modified" if modified else "")
        self._update_window_title()
    
    def _prompt_save_changes(self) -> bool:
        """
        Prompt user to save changes if document is modified.
        
        Returns:
            True if safe to proceed, False if operation should be cancelled.
        """
        if not self._editor.is_modified:
            return True
        
        result = QMessageBox.warning(
            self,
            "Unsaved Changes",
            f"Do you want to save changes to {self._editor.file_name}?",
            QMessageBox.StandardButton.Save |
            QMessageBox.StandardButton.Discard |
            QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Save
        )
        
        if result == QMessageBox.StandardButton.Save:
            return self._on_save()
        elif result == QMessageBox.StandardButton.Discard:
            return True
        else:
            return False
    
    def _on_new(self):
        """Handle File > New action."""
        if not self._prompt_save_changes():
            return
        
        self._editor.new_document()
        self._update_window_title()
        self._update_status_bar()
    
    def _on_open(self):
        """Handle File > Open action."""
        if not self._prompt_save_changes():
            return
        
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
            self._editor.set_content(result.content, file_path)
            self._update_window_title()
            self._update_status_bar()
        else:
            self._show_error("Open Error", result.error_message)
    
    def _on_save(self) -> bool:
        """
        Handle File > Save action.
        
        Returns:
            True if save succeeded, False otherwise.
        """
        if self._editor.current_file_path:
            return self._save_to_path(self._editor.current_file_path)
        else:
            return self._on_save_as()
    
    def _on_save_as(self) -> bool:
        """
        Handle File > Save As action.
        
        Returns:
            True if save succeeded, False otherwise.
        """
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save File",
            "",
            "Text Files (*.txt);;All Files (*)"
        )
        
        if not file_path:
            return False
        
        return self._save_to_path(file_path)
    
    def _save_to_path(self, file_path: str) -> bool:
        """
        Save document to the specified path.
        
        Args:
            file_path: Path to save the file.
            
        Returns:
            True if save succeeded, False otherwise.
        """
        content = self._editor.get_content()
        result = self._file_handler.write_file(file_path, content)
        
        if result.success:
            self._editor.mark_as_saved(file_path)
            self._update_window_title()
            self._update_status_bar()
            return True
        else:
            self._show_error("Save Error", result.error_message)
            return False
    
    def _on_toggle_word_wrap(self, checked: bool):
        """Handle View > Word Wrap toggle."""
        self._editor.set_word_wrap(checked)
    
    def _on_toggle_status_bar(self, checked: bool):
        """Handle View > Status Bar toggle."""
        self._status_bar.setVisible(checked)
    
    def _on_about(self):
        """Handle Help > About action."""
        QMessageBox.about(
            self,
            "About TextEdit",
            "TextEdit\n\n"
            "A simple, cross-platform text editor.\n\n"
            "Built with Python and Qt (PySide6)."
        )
    
    def _show_error(self, title: str, message: str):
        """Show an error dialog."""
        QMessageBox.critical(self, title, message)
    
    def closeEvent(self, event):
        """Handle window close event."""
        if self._prompt_save_changes():
            event.accept()
        else:
            event.ignore()
