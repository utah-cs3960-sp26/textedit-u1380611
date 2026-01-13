"""
Theme Manager Module

Provides dark and light themes for the application.
"""

from enum import Enum
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor


class Theme(Enum):
    DARK = "dark"
    LIGHT = "light"
    AQUAMARINE = "aquamarine"
    MIDNIGHT_BLUE = "midnight_blue"


DARK_STYLESHEET = """
QMainWindow {
    background-color: #1e1e1e;
}

QMenuBar {
    background-color: #2d2d2d;
    color: #cccccc;
    border-bottom: 1px solid #3d3d3d;
    padding: 4px 0px;
}

QMenuBar::item {
    background-color: transparent;
    padding: 6px 12px;
    border-radius: 4px;
    margin: 0px 2px;
}

QMenuBar::item:selected {
    background-color: #404040;
}

QMenuBar::item:pressed {
    background-color: #505050;
}

QMenu {
    background-color: #2d2d2d;
    color: #cccccc;
    border: 1px solid #3d3d3d;
    border-radius: 8px;
    padding: 6px;
}

QMenu::item {
    padding: 8px 32px 8px 16px;
    border-radius: 4px;
    margin: 2px 4px;
}

QMenu::item:selected {
    background-color: #404040;
}

QMenu::separator {
    height: 1px;
    background-color: #3d3d3d;
    margin: 6px 8px;
}

QMenu::indicator {
    width: 16px;
    height: 16px;
    margin-left: 8px;
}

QMenu::indicator:checked {
    background-color: #0078d4;
    border-radius: 3px;
}

QTabBar {
    background-color: #252526;
    border: none;
}

QTabBar::tab {
    background-color: #2d2d2d;
    color: #969696;
    padding: 8px 16px 8px 24px;
    margin-right: 1px;
    border: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
}

QTabBar::tab:selected {
    background-color: #1e1e1e;
    color: #ffffff;
}

QTabBar::tab:hover:!selected {
    background-color: #383838;
    color: #cccccc;
}

QTabBar::close-button {
    subcontrol-position: right;
    padding: 2px;
    margin-right: 4px;
    border-radius: 4px;
    width: 16px;
    height: 16px;
}

QTabBar::close-button:hover {
    background-color: #c42b1c;
}

QToolButton {
    background-color: transparent;
    color: #cccccc;
    border: none;
    border-radius: 4px;
    padding: 4px;
    font-size: 14px;
    font-weight: bold;
}

QToolButton:hover {
    background-color: #404040;
}

QToolButton:pressed {
    background-color: #505050;
}

QPlainTextEdit {
    background-color: #1e1e1e;
    color: #d4d4d4;
    border: none;
    selection-background-color: #264f78;
    selection-color: #ffffff;
    font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
    font-size: 14px;
    padding: 8px;
}

QStatusBar {
    background-color: #007acc;
    color: #ffffff;
    border: none;
    padding: 0px;
    min-height: 24px;
}

QStatusBar::item {
    border: none;
}

QStatusBar QLabel {
    color: #ffffff;
    padding: 4px 12px;
    font-size: 12px;
}

QScrollBar:vertical {
    background-color: #1e1e1e;
    width: 14px;
    border: none;
}

QScrollBar::handle:vertical {
    background-color: #5a5a5a;
    min-height: 30px;
    border-radius: 7px;
    margin: 2px;
}

QScrollBar::handle:vertical:hover {
    background-color: #787878;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {
    background: none;
}

QScrollBar:horizontal {
    background-color: #1e1e1e;
    height: 14px;
    border: none;
}

QScrollBar::handle:horizontal {
    background-color: #5a5a5a;
    min-width: 30px;
    border-radius: 7px;
    margin: 2px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #787878;
}

QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {
    width: 0px;
}

QScrollBar::add-page:horizontal,
QScrollBar::sub-page:horizontal {
    background: none;
}

QMessageBox {
    background-color: #2d2d2d;
}

QMessageBox QLabel {
    color: #cccccc;
}

QMessageBox QPushButton {
    background-color: #0078d4;
    color: #ffffff;
    border: none;
    border-radius: 4px;
    padding: 8px 20px;
    min-width: 80px;
}

QMessageBox QPushButton:hover {
    background-color: #1e8ae6;
}

QMessageBox QPushButton:pressed {
    background-color: #006cbd;
}

QFileDialog {
    background-color: #2d2d2d;
    color: #cccccc;
}

QSplitter::handle {
    background-color: #3d3d3d;
}

QSplitter::handle:horizontal {
    width: 2px;
}

QSplitter::handle:vertical {
    height: 2px;
}

QSplitter::handle:hover {
    background-color: #0078d4;
}
"""

LIGHT_STYLESHEET = """
QMainWindow {
    background-color: #ffffff;
}

QMenuBar {
    background-color: #f3f3f3;
    color: #333333;
    border-bottom: 1px solid #e0e0e0;
    padding: 4px 0px;
}

QMenuBar::item {
    background-color: transparent;
    padding: 6px 12px;
    border-radius: 4px;
    margin: 0px 2px;
}

QMenuBar::item:selected {
    background-color: #e0e0e0;
}

QMenuBar::item:pressed {
    background-color: #d0d0d0;
}

QMenu {
    background-color: #ffffff;
    color: #333333;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 6px;
}

QMenu::item {
    padding: 8px 32px 8px 16px;
    border-radius: 4px;
    margin: 2px 4px;
}

QMenu::item:selected {
    background-color: #e8e8e8;
}

QMenu::separator {
    height: 1px;
    background-color: #e0e0e0;
    margin: 6px 8px;
}

QMenu::indicator {
    width: 16px;
    height: 16px;
    margin-left: 8px;
}

QMenu::indicator:checked {
    background-color: #0078d4;
    border-radius: 3px;
}

QTabBar {
    background-color: #f3f3f3;
    border: none;
}

QTabBar::tab {
    background-color: #e8e8e8;
    color: #666666;
    padding: 8px 16px 8px 24px;
    margin-right: 1px;
    border: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
}

QTabBar::tab:selected {
    background-color: #ffffff;
    color: #333333;
}

QTabBar::tab:hover:!selected {
    background-color: #d8d8d8;
    color: #444444;
}

QTabBar::close-button {
    subcontrol-position: right;
    padding: 2px;
    margin-right: 4px;
    border-radius: 4px;
    width: 16px;
    height: 16px;
}

QTabBar::close-button:hover {
    background-color: #c42b1c;
}

QToolButton {
    background-color: transparent;
    color: #333333;
    border: none;
    border-radius: 4px;
    padding: 4px;
    font-size: 14px;
    font-weight: bold;
}

QToolButton:hover {
    background-color: #e0e0e0;
}

QToolButton:pressed {
    background-color: #d0d0d0;
}

QPlainTextEdit {
    background-color: #ffffff;
    color: #333333;
    border: none;
    selection-background-color: #add6ff;
    selection-color: #000000;
    font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
    font-size: 14px;
    padding: 8px;
}

QStatusBar {
    background-color: #0078d4;
    color: #ffffff;
    border: none;
    padding: 0px;
    min-height: 24px;
}

QStatusBar::item {
    border: none;
}

QStatusBar QLabel {
    color: #ffffff;
    padding: 4px 12px;
    font-size: 12px;
}

QScrollBar:vertical {
    background-color: #f3f3f3;
    width: 14px;
    border: none;
}

QScrollBar::handle:vertical {
    background-color: #c1c1c1;
    min-height: 30px;
    border-radius: 7px;
    margin: 2px;
}

QScrollBar::handle:vertical:hover {
    background-color: #a8a8a8;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {
    background: none;
}

QScrollBar:horizontal {
    background-color: #f3f3f3;
    height: 14px;
    border: none;
}

QScrollBar::handle:horizontal {
    background-color: #c1c1c1;
    min-width: 30px;
    border-radius: 7px;
    margin: 2px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #a8a8a8;
}

QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {
    width: 0px;
}

QScrollBar::add-page:horizontal,
QScrollBar::sub-page:horizontal {
    background: none;
}

QMessageBox {
    background-color: #ffffff;
}

QMessageBox QLabel {
    color: #333333;
}

QMessageBox QPushButton {
    background-color: #0078d4;
    color: #ffffff;
    border: none;
    border-radius: 4px;
    padding: 8px 20px;
    min-width: 80px;
}

QMessageBox QPushButton:hover {
    background-color: #1e8ae6;
}

QMessageBox QPushButton:pressed {
    background-color: #006cbd;
}

QFileDialog {
    background-color: #ffffff;
    color: #333333;
}

QSplitter::handle {
    background-color: #e0e0e0;
}

QSplitter::handle:horizontal {
    width: 2px;
}

QSplitter::handle:vertical {
    height: 2px;
}

QSplitter::handle:hover {
    background-color: #0078d4;
}
"""

AQUAMARINE_STYLESHEET = """
QMainWindow {
    background-color: #1a2f2f;
}

QMenuBar {
    background-color: #243d3d;
    color: #e0f0f0;
    border-bottom: 1px solid #2d4a4a;
    padding: 4px 0px;
}

QMenuBar::item {
    background-color: transparent;
    padding: 6px 12px;
    border-radius: 4px;
    margin: 0px 2px;
}

QMenuBar::item:selected {
    background-color: #2d5a5a;
}

QMenuBar::item:pressed {
    background-color: #3d6a6a;
}

QMenu {
    background-color: #243d3d;
    color: #e0f0f0;
    border: 1px solid #2d4a4a;
    border-radius: 8px;
    padding: 6px;
}

QMenu::item {
    padding: 8px 32px 8px 16px;
    border-radius: 4px;
    margin: 2px 4px;
}

QMenu::item:selected {
    background-color: #2d5a5a;
}

QMenu::separator {
    height: 1px;
    background-color: #2d4a4a;
    margin: 6px 8px;
}

QMenu::indicator {
    width: 16px;
    height: 16px;
    margin-left: 8px;
}

QMenu::indicator:checked {
    background-color: #ff8c42;
    border-radius: 3px;
}

QTabBar {
    background-color: #1f3535;
    border: none;
}

QTabBar::tab {
    background-color: #243d3d;
    color: #80b0b0;
    padding: 8px 16px 8px 24px;
    margin-right: 1px;
    border: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
}

QTabBar::tab:selected {
    background-color: #1a2f2f;
    color: #40e0d0;
}

QTabBar::tab:hover:!selected {
    background-color: #2d4a4a;
    color: #a0d0d0;
}

QTabBar::close-button {
    subcontrol-position: right;
    padding: 2px;
    margin-right: 4px;
    border-radius: 4px;
    width: 16px;
    height: 16px;
}

QTabBar::close-button:hover {
    background-color: #ff8c42;
}

QToolButton {
    background-color: transparent;
    color: #e0f0f0;
    border: none;
    border-radius: 4px;
    padding: 4px;
    font-size: 14px;
    font-weight: bold;
}

QToolButton:hover {
    background-color: #2d5a5a;
}

QToolButton:pressed {
    background-color: #3d6a6a;
}

QPlainTextEdit {
    background-color: #1a2f2f;
    color: #e0f0f0;
    border: none;
    selection-background-color: #2d6a6a;
    selection-color: #ffffff;
    font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
    font-size: 14px;
    padding: 8px;
}

QStatusBar {
    background-color: #40e0d0;
    color: #1a2f2f;
    border: none;
    padding: 0px;
    min-height: 24px;
}

QStatusBar::item {
    border: none;
}

QStatusBar QLabel {
    color: #1a2f2f;
    padding: 4px 12px;
    font-size: 12px;
    font-weight: bold;
}

QScrollBar:vertical {
    background-color: #1a2f2f;
    width: 14px;
    border: none;
}

QScrollBar::handle:vertical {
    background-color: #3d6a6a;
    min-height: 30px;
    border-radius: 7px;
    margin: 2px;
}

QScrollBar::handle:vertical:hover {
    background-color: #40e0d0;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {
    background: none;
}

QScrollBar:horizontal {
    background-color: #1a2f2f;
    height: 14px;
    border: none;
}

QScrollBar::handle:horizontal {
    background-color: #3d6a6a;
    min-width: 30px;
    border-radius: 7px;
    margin: 2px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #40e0d0;
}

QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {
    width: 0px;
}

QScrollBar::add-page:horizontal,
QScrollBar::sub-page:horizontal {
    background: none;
}

QMessageBox {
    background-color: #243d3d;
}

QMessageBox QLabel {
    color: #e0f0f0;
}

QMessageBox QPushButton {
    background-color: #ff8c42;
    color: #1a2f2f;
    border: none;
    border-radius: 4px;
    padding: 8px 20px;
    min-width: 80px;
    font-weight: bold;
}

QMessageBox QPushButton:hover {
    background-color: #ffa060;
}

QMessageBox QPushButton:pressed {
    background-color: #e07830;
}

QFileDialog {
    background-color: #243d3d;
    color: #e0f0f0;
}

QSplitter::handle {
    background-color: #2d4a4a;
}

QSplitter::handle:horizontal {
    width: 2px;
}

QSplitter::handle:vertical {
    height: 2px;
}

QSplitter::handle:hover {
    background-color: #40e0d0;
}
"""

MIDNIGHT_BLUE_STYLESHEET = """
QMainWindow {
    background-color: #0d1117;
}

QMenuBar {
    background-color: #161b22;
    color: #c9d1d9;
    border-bottom: 1px solid #21262d;
    padding: 4px 0px;
}

QMenuBar::item {
    background-color: transparent;
    padding: 6px 12px;
    border-radius: 4px;
    margin: 0px 2px;
}

QMenuBar::item:selected {
    background-color: #21262d;
}

QMenuBar::item:pressed {
    background-color: #30363d;
}

QMenu {
    background-color: #161b22;
    color: #c9d1d9;
    border: 1px solid #21262d;
    border-radius: 8px;
    padding: 6px;
}

QMenu::item {
    padding: 8px 32px 8px 16px;
    border-radius: 4px;
    margin: 2px 4px;
}

QMenu::item:selected {
    background-color: #21262d;
}

QMenu::separator {
    height: 1px;
    background-color: #21262d;
    margin: 6px 8px;
}

QMenu::indicator {
    width: 16px;
    height: 16px;
    margin-left: 8px;
}

QMenu::indicator:checked {
    background-color: #58a6ff;
    border-radius: 3px;
}

QTabBar {
    background-color: #0d1117;
    border: none;
}

QTabBar::tab {
    background-color: #161b22;
    color: #8b949e;
    padding: 8px 16px 8px 24px;
    margin-right: 1px;
    border: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
}

QTabBar::tab:selected {
    background-color: #0d1117;
    color: #f0f6fc;
    border-top: 2px solid #58a6ff;
}

QTabBar::tab:hover:!selected {
    background-color: #21262d;
    color: #c9d1d9;
}

QTabBar::close-button {
    subcontrol-position: right;
    padding: 2px;
    margin-right: 4px;
    border-radius: 4px;
    width: 16px;
    height: 16px;
}

QTabBar::close-button:hover {
    background-color: #f85149;
}

QToolButton {
    background-color: transparent;
    color: #c9d1d9;
    border: none;
    border-radius: 4px;
    padding: 4px;
    font-size: 14px;
    font-weight: bold;
}

QToolButton:hover {
    background-color: #21262d;
}

QToolButton:pressed {
    background-color: #30363d;
}

QPlainTextEdit {
    background-color: #0d1117;
    color: #c9d1d9;
    border: none;
    selection-background-color: #264f78;
    selection-color: #ffffff;
    font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
    font-size: 14px;
    padding: 8px;
}

QStatusBar {
    background-color: #238636;
    color: #ffffff;
    border: none;
    padding: 0px;
    min-height: 24px;
}

QStatusBar::item {
    border: none;
}

QStatusBar QLabel {
    color: #ffffff;
    padding: 4px 12px;
    font-size: 12px;
}

QScrollBar:vertical {
    background-color: #0d1117;
    width: 14px;
    border: none;
}

QScrollBar::handle:vertical {
    background-color: #30363d;
    min-height: 30px;
    border-radius: 7px;
    margin: 2px;
}

QScrollBar::handle:vertical:hover {
    background-color: #484f58;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {
    background: none;
}

QScrollBar:horizontal {
    background-color: #0d1117;
    height: 14px;
    border: none;
}

QScrollBar::handle:horizontal {
    background-color: #30363d;
    min-width: 30px;
    border-radius: 7px;
    margin: 2px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #484f58;
}

QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {
    width: 0px;
}

QScrollBar::add-page:horizontal,
QScrollBar::sub-page:horizontal {
    background: none;
}

QMessageBox {
    background-color: #161b22;
}

QMessageBox QLabel {
    color: #c9d1d9;
}

QMessageBox QPushButton {
    background-color: #238636;
    color: #ffffff;
    border: none;
    border-radius: 4px;
    padding: 8px 20px;
    min-width: 80px;
}

QMessageBox QPushButton:hover {
    background-color: #2ea043;
}

QMessageBox QPushButton:pressed {
    background-color: #196c2e;
}

QFileDialog {
    background-color: #161b22;
    color: #c9d1d9;
}

QSplitter::handle {
    background-color: #21262d;
}

QSplitter::handle:horizontal {
    width: 2px;
}

QSplitter::handle:vertical {
    height: 2px;
}

QSplitter::handle:hover {
    background-color: #58a6ff;
}
"""


class ThemeManager:
    """Manages application themes."""
    
    _instance = None
    _current_theme: Theme = Theme.MIDNIGHT_BLUE
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @property
    def current_theme(self) -> Theme:
        return self._current_theme
    
    def apply_theme(self, theme: Theme):
        """Apply a theme to the application."""
        self._current_theme = theme
        app = QApplication.instance()
        if app:
            stylesheets = {
                Theme.DARK: DARK_STYLESHEET,
                Theme.LIGHT: LIGHT_STYLESHEET,
                Theme.AQUAMARINE: AQUAMARINE_STYLESHEET,
                Theme.MIDNIGHT_BLUE: MIDNIGHT_BLUE_STYLESHEET,
            }
            app.setStyleSheet(stylesheets.get(theme, DARK_STYLESHEET))
    
    def toggle_theme(self):
        """Toggle between dark and light themes."""
        if self._current_theme == Theme.DARK:
            self.apply_theme(Theme.LIGHT)
        else:
            self.apply_theme(Theme.DARK)
