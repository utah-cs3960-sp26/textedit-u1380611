"""
Theme Manager Module

Provides dark and light themes for the application with custom theme support.
"""

import json
import os
from enum import Enum
from typing import Optional
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor


class Theme(Enum):
    DARK = "dark"
    LIGHT = "light"
    AQUAMARINE = "aquamarine"
    MIDNIGHT_BLUE = "midnight_blue"
    CUSTOM = "custom"


def get_themes_dir() -> str:
    """Get the directory for storing custom themes."""
    config_dir = os.path.join(os.path.expanduser("~"), ".textedit")
    themes_dir = os.path.join(config_dir, "themes")
    os.makedirs(themes_dir, exist_ok=True)
    return themes_dir


def get_settings_path() -> str:
    """Get the path for settings file."""
    config_dir = os.path.join(os.path.expanduser("~"), ".textedit")
    os.makedirs(config_dir, exist_ok=True)
    return os.path.join(config_dir, "settings.json")


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

QTreeView {
    background-color: #252526;
    color: #cccccc;
    border: none;
    outline: none;
}

QTreeView::item {
    padding: 4px 8px;
    border-radius: 4px;
}

QTreeView::item:hover {
    background-color: #2a2d2e;
}

QTreeView::item:selected {
    background-color: #094771;
    color: #ffffff;
}

QTreeView::branch:has-children:!has-siblings:closed,
QTreeView::branch:closed:has-children:has-siblings {
    image: none;
    border-image: none;
}

QTreeView::branch:open:has-children:!has-siblings,
QTreeView::branch:open:has-children:has-siblings {
    image: none;
    border-image: none;
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

QTreeView {
    background-color: #f3f3f3;
    color: #333333;
    border: none;
    outline: none;
}

QTreeView::item {
    padding: 4px 8px;
    border-radius: 4px;
}

QTreeView::item:hover {
    background-color: #e8e8e8;
}

QTreeView::item:selected {
    background-color: #0078d4;
    color: #ffffff;
}

QTreeView::branch:has-children:!has-siblings:closed,
QTreeView::branch:closed:has-children:has-siblings {
    image: none;
    border-image: none;
}

QTreeView::branch:open:has-children:!has-siblings,
QTreeView::branch:open:has-children:has-siblings {
    image: none;
    border-image: none;
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

QTreeView {
    background-color: #1a2f2f;
    color: #e0f0f0;
    border: none;
    outline: none;
}

QTreeView::item {
    padding: 4px 8px;
    border-radius: 4px;
}

QTreeView::item:hover {
    background-color: #243d3d;
}

QTreeView::item:selected {
    background-color: #2d5a5a;
    color: #40e0d0;
}

QTreeView::branch:has-children:!has-siblings:closed,
QTreeView::branch:closed:has-children:has-siblings {
    image: none;
    border-image: none;
}

QTreeView::branch:open:has-children:!has-siblings,
QTreeView::branch:open:has-children:has-siblings {
    image: none;
    border-image: none;
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

QTreeView {
    background-color: #0d1117;
    color: #c9d1d9;
    border: none;
    outline: none;
}

QTreeView::item {
    padding: 4px 8px;
    border-radius: 4px;
}

QTreeView::item:hover {
    background-color: #161b22;
}

QTreeView::item:selected {
    background-color: #1f6feb;
    color: #ffffff;
}

QTreeView::branch:has-children:!has-siblings:closed,
QTreeView::branch:closed:has-children:has-siblings {
    image: none;
    border-image: none;
}

QTreeView::branch:open:has-children:!has-siblings,
QTreeView::branch:open:has-children:has-siblings {
    image: none;
    border-image: none;
}
"""


BUILTIN_THEME_COLORS = {
    "Dark": {
        "main_background": "#1e1e1e",
        "editor_background": "#1e1e1e",
        "editor_text": "#d4d4d4",
        "selection_background": "#264f78",
        "selection_text": "#ffffff",
        "menubar_background": "#2d2d2d",
        "menubar_text": "#cccccc",
        "menu_background": "#2d2d2d",
        "menu_text": "#cccccc",
        "menu_hover": "#404040",
        "tab_background": "#2d2d2d",
        "tab_text": "#969696",
        "tab_active_background": "#1e1e1e",
        "tab_active_text": "#ffffff",
        "status_bar_background": "#007acc",
        "status_bar_text": "#ffffff",
        "scrollbar_background": "#1e1e1e",
        "scrollbar_handle": "#5a5a5a",
        "tree_background": "#252526",
        "tree_text": "#cccccc",
        "tree_selection": "#094771",
        "border_color": "#3d3d3d",
        "accent_color": "#0078d4",
        "line_number_bg": "#1e1e1e",
        "line_number_text": "#858585",
        "line_number_current": "#c6c6c6",
        "line_number_current_bg": "#282828",
    },
    "Light": {
        "main_background": "#ffffff",
        "editor_background": "#ffffff",
        "editor_text": "#333333",
        "selection_background": "#add6ff",
        "selection_text": "#000000",
        "menubar_background": "#f3f3f3",
        "menubar_text": "#333333",
        "menu_background": "#ffffff",
        "menu_text": "#333333",
        "menu_hover": "#e8e8e8",
        "tab_background": "#e8e8e8",
        "tab_text": "#666666",
        "tab_active_background": "#ffffff",
        "tab_active_text": "#333333",
        "status_bar_background": "#0078d4",
        "status_bar_text": "#ffffff",
        "scrollbar_background": "#f3f3f3",
        "scrollbar_handle": "#c1c1c1",
        "tree_background": "#f3f3f3",
        "tree_text": "#333333",
        "tree_selection": "#0078d4",
        "border_color": "#e0e0e0",
        "accent_color": "#0078d4",
        "line_number_bg": "#f3f3f3",
        "line_number_text": "#999999",
        "line_number_current": "#333333",
        "line_number_current_bg": "#e8e8e8",
    },
    "Aquamarine": {
        "main_background": "#1a2f2f",
        "editor_background": "#1a2f2f",
        "editor_text": "#e0f0f0",
        "selection_background": "#2d6a6a",
        "selection_text": "#ffffff",
        "menubar_background": "#243d3d",
        "menubar_text": "#e0f0f0",
        "menu_background": "#243d3d",
        "menu_text": "#e0f0f0",
        "menu_hover": "#2d5a5a",
        "tab_background": "#243d3d",
        "tab_text": "#80b0b0",
        "tab_active_background": "#1a2f2f",
        "tab_active_text": "#40e0d0",
        "status_bar_background": "#40e0d0",
        "status_bar_text": "#1a2f2f",
        "scrollbar_background": "#1a2f2f",
        "scrollbar_handle": "#3d6a6a",
        "tree_background": "#1a2f2f",
        "tree_text": "#e0f0f0",
        "tree_selection": "#2d5a5a",
        "border_color": "#2d4a4a",
        "accent_color": "#40e0d0",
        "line_number_bg": "#1a2f2f",
        "line_number_text": "#5a8a8a",
        "line_number_current": "#40e0d0",
        "line_number_current_bg": "#243d3d",
    },
    "Midnight Blue": {
        "main_background": "#0d1117",
        "editor_background": "#0d1117",
        "editor_text": "#c9d1d9",
        "selection_background": "#264f78",
        "selection_text": "#ffffff",
        "menubar_background": "#161b22",
        "menubar_text": "#c9d1d9",
        "menu_background": "#161b22",
        "menu_text": "#c9d1d9",
        "menu_hover": "#21262d",
        "tab_background": "#161b22",
        "tab_text": "#8b949e",
        "tab_active_background": "#0d1117",
        "tab_active_text": "#f0f6fc",
        "status_bar_background": "#238636",
        "status_bar_text": "#ffffff",
        "scrollbar_background": "#0d1117",
        "scrollbar_handle": "#30363d",
        "tree_background": "#0d1117",
        "tree_text": "#c9d1d9",
        "tree_selection": "#1f6feb",
        "border_color": "#21262d",
        "accent_color": "#58a6ff",
        "line_number_bg": "#0d1117",
        "line_number_text": "#6e7681",
        "line_number_current": "#c9d1d9",
        "line_number_current_bg": "#161b22",
    },
}


def generate_stylesheet_from_colors(colors: dict) -> str:
    """Generate a Qt stylesheet from color dictionary."""
    return f"""
QMainWindow {{
    background-color: {colors.get('main_background', '#1e1e1e')};
}}

QMenuBar {{
    background-color: {colors.get('menubar_background', '#2d2d2d')};
    color: {colors.get('menubar_text', '#cccccc')};
    border-bottom: 1px solid {colors.get('border_color', '#3d3d3d')};
    padding: 4px 0px;
}}

QMenuBar::item {{
    background-color: transparent;
    padding: 6px 12px;
    border-radius: 4px;
    margin: 0px 2px;
}}

QMenuBar::item:selected {{
    background-color: {colors.get('menu_hover', '#404040')};
}}

QMenuBar::item:pressed {{
    background-color: {colors.get('menu_hover', '#404040')};
}}

QMenu {{
    background-color: {colors.get('menu_background', '#2d2d2d')};
    color: {colors.get('menu_text', '#cccccc')};
    border: 1px solid {colors.get('border_color', '#3d3d3d')};
    border-radius: 8px;
    padding: 6px;
}}

QMenu::item {{
    padding: 8px 32px 8px 16px;
    border-radius: 4px;
    margin: 2px 4px;
}}

QMenu::item:selected {{
    background-color: {colors.get('menu_hover', '#404040')};
}}

QMenu::separator {{
    height: 1px;
    background-color: {colors.get('border_color', '#3d3d3d')};
    margin: 6px 8px;
}}

QMenu::indicator {{
    width: 16px;
    height: 16px;
    margin-left: 8px;
}}

QMenu::indicator:checked {{
    background-color: {colors.get('accent_color', '#0078d4')};
    border-radius: 3px;
}}

QTabBar {{
    background-color: {colors.get('main_background', '#1e1e1e')};
    border: none;
}}

QTabBar::tab {{
    background-color: {colors.get('tab_background', '#2d2d2d')};
    color: {colors.get('tab_text', '#969696')};
    padding: 8px 16px 8px 24px;
    margin-right: 1px;
    border: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
}}

QTabBar::tab:selected {{
    background-color: {colors.get('tab_active_background', '#1e1e1e')};
    color: {colors.get('tab_active_text', '#ffffff')};
    border-top: 2px solid {colors.get('accent_color', '#0078d4')};
}}

QTabBar::tab:hover:!selected {{
    background-color: {colors.get('menu_hover', '#404040')};
    color: {colors.get('menubar_text', '#cccccc')};
}}

QTabBar::close-button {{
    subcontrol-position: right;
    padding: 2px;
    margin-right: 4px;
    border-radius: 4px;
    width: 16px;
    height: 16px;
}}

QTabBar::close-button:hover {{
    background-color: #c42b1c;
}}

QToolButton {{
    background-color: transparent;
    color: {colors.get('menubar_text', '#cccccc')};
    border: none;
    border-radius: 4px;
    padding: 4px;
    font-size: 14px;
    font-weight: bold;
}}

QToolButton:hover {{
    background-color: {colors.get('menu_hover', '#404040')};
}}

QToolButton:pressed {{
    background-color: {colors.get('menu_hover', '#404040')};
}}

QPlainTextEdit {{
    background-color: {colors.get('editor_background', '#1e1e1e')};
    color: {colors.get('editor_text', '#d4d4d4')};
    border: none;
    selection-background-color: {colors.get('selection_background', '#264f78')};
    selection-color: {colors.get('selection_text', '#ffffff')};
    font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
    font-size: 14px;
    padding: 8px;
}}

QStatusBar {{
    background-color: {colors.get('status_bar_background', '#007acc')};
    color: {colors.get('status_bar_text', '#ffffff')};
    border: none;
    padding: 0px;
    min-height: 24px;
}}

QStatusBar::item {{
    border: none;
}}

QStatusBar QLabel {{
    color: {colors.get('status_bar_text', '#ffffff')};
    padding: 4px 12px;
    font-size: 12px;
}}

QScrollBar:vertical {{
    background-color: {colors.get('scrollbar_background', '#1e1e1e')};
    width: 14px;
    border: none;
}}

QScrollBar::handle:vertical {{
    background-color: {colors.get('scrollbar_handle', '#5a5a5a')};
    min-height: 30px;
    border-radius: 7px;
    margin: 2px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {colors.get('accent_color', '#0078d4')};
}}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {{
    background: none;
}}

QScrollBar:horizontal {{
    background-color: {colors.get('scrollbar_background', '#1e1e1e')};
    height: 14px;
    border: none;
}}

QScrollBar::handle:horizontal {{
    background-color: {colors.get('scrollbar_handle', '#5a5a5a')};
    min-width: 30px;
    border-radius: 7px;
    margin: 2px;
}}

QScrollBar::handle:horizontal:hover {{
    background-color: {colors.get('accent_color', '#0078d4')};
}}

QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {{
    width: 0px;
}}

QScrollBar::add-page:horizontal,
QScrollBar::sub-page:horizontal {{
    background: none;
}}

QMessageBox {{
    background-color: {colors.get('menu_background', '#2d2d2d')};
}}

QMessageBox QLabel {{
    color: {colors.get('menu_text', '#cccccc')};
}}

QMessageBox QPushButton {{
    background-color: {colors.get('accent_color', '#0078d4')};
    color: {colors.get('status_bar_text', '#ffffff')};
    border: none;
    border-radius: 4px;
    padding: 8px 20px;
    min-width: 80px;
}}

QMessageBox QPushButton:hover {{
    background-color: {colors.get('accent_color', '#0078d4')};
}}

QMessageBox QPushButton:pressed {{
    background-color: {colors.get('accent_color', '#0078d4')};
}}

QFileDialog {{
    background-color: {colors.get('menu_background', '#2d2d2d')};
    color: {colors.get('menu_text', '#cccccc')};
}}

QSplitter::handle {{
    background-color: {colors.get('border_color', '#3d3d3d')};
}}

QSplitter::handle:horizontal {{
    width: 2px;
}}

QSplitter::handle:vertical {{
    height: 2px;
}}

QSplitter::handle:hover {{
    background-color: {colors.get('accent_color', '#0078d4')};
}}

QTreeView {{
    background-color: {colors.get('tree_background', '#252526')};
    color: {colors.get('tree_text', '#cccccc')};
    border: none;
    outline: none;
}}

QTreeView::item {{
    padding: 4px 8px;
    border-radius: 4px;
}}

QTreeView::item:hover {{
    background-color: {colors.get('menu_hover', '#404040')};
}}

QTreeView::item:selected {{
    background-color: {colors.get('tree_selection', '#094771')};
    color: #ffffff;
}}

QTreeView::branch:has-children:!has-siblings:closed,
QTreeView::branch:closed:has-children:has-siblings {{
    image: none;
    border-image: none;
}}

QTreeView::branch:open:has-children:!has-siblings,
QTreeView::branch:open:has-children:has-siblings {{
    image: none;
    border-image: none;
}}

QDialog {{
    background-color: {colors.get('main_background', '#1e1e1e')};
}}

QLabel {{
    color: {colors.get('editor_text', '#d4d4d4')};
}}

QLineEdit {{
    background-color: {colors.get('editor_background', '#1e1e1e')};
    color: {colors.get('editor_text', '#d4d4d4')};
    border: 1px solid {colors.get('border_color', '#3d3d3d')};
    border-radius: 4px;
    padding: 6px;
}}

QLineEdit:focus {{
    border: 1px solid {colors.get('accent_color', '#0078d4')};
}}

QPushButton {{
    background-color: {colors.get('tab_background', '#2d2d2d')};
    color: {colors.get('editor_text', '#d4d4d4')};
    border: 1px solid {colors.get('border_color', '#3d3d3d')};
    border-radius: 4px;
    padding: 8px 16px;
}}

QPushButton:hover {{
    background-color: {colors.get('menu_hover', '#404040')};
}}

QPushButton:pressed {{
    background-color: {colors.get('accent_color', '#0078d4')};
}}

QListWidget {{
    background-color: {colors.get('editor_background', '#1e1e1e')};
    color: {colors.get('editor_text', '#d4d4d4')};
    border: 1px solid {colors.get('border_color', '#3d3d3d')};
    border-radius: 4px;
}}

QListWidget::item {{
    padding: 6px;
}}

QListWidget::item:selected {{
    background-color: {colors.get('tree_selection', '#094771')};
    color: #ffffff;
}}

QListWidget::item:hover {{
    background-color: {colors.get('menu_hover', '#404040')};
}}

QGroupBox {{
    color: {colors.get('editor_text', '#d4d4d4')};
    border: 1px solid {colors.get('border_color', '#3d3d3d')};
    border-radius: 4px;
    margin-top: 12px;
    padding-top: 8px;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
}}

QTabWidget::pane {{
    border: 1px solid {colors.get('border_color', '#3d3d3d')};
    background-color: {colors.get('main_background', '#1e1e1e')};
}}

QScrollArea {{
    background-color: {colors.get('main_background', '#1e1e1e')};
    border: none;
}}
"""


class ThemeManager:
    """Manages application themes with custom theme support."""
    
    _instance = None
    _current_theme: Theme = Theme.MIDNIGHT_BLUE
    _current_theme_name: str = "Midnight Blue"
    _custom_themes: dict = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_custom_themes()
            cls._instance._load_settings()
        return cls._instance
    
    def _load_custom_themes(self):
        """Load custom themes from disk."""
        themes_dir = get_themes_dir()
        self._custom_themes = {}
        
        if os.path.exists(themes_dir):
            for filename in os.listdir(themes_dir):
                if filename.endswith(".json"):
                    theme_path = os.path.join(themes_dir, filename)
                    try:
                        with open(theme_path, "r") as f:
                            theme_data = json.load(f)
                            name = theme_data.get("name", filename[:-5])
                            self._custom_themes[name] = theme_data.get("colors", {})
                    except (json.JSONDecodeError, IOError):
                        pass
    
    def _load_settings(self):
        """Load application settings."""
        settings_path = get_settings_path()
        if os.path.exists(settings_path):
            try:
                with open(settings_path, "r") as f:
                    settings = json.load(f)
                    self._current_theme_name = settings.get("theme", "Midnight Blue")
            except (json.JSONDecodeError, IOError):
                pass
    
    def _save_settings(self):
        """Save application settings."""
        settings_path = get_settings_path()
        try:
            with open(settings_path, "w") as f:
                json.dump({"theme": self._current_theme_name}, f)
        except IOError:
            pass
    
    @property
    def current_theme(self) -> Theme:
        return self._current_theme
    
    @property
    def current_theme_name(self) -> str:
        return self._current_theme_name
    
    def get_builtin_theme_names(self) -> list:
        """Get list of built-in theme names."""
        return list(BUILTIN_THEME_COLORS.keys())
    
    def get_custom_theme_names(self) -> list:
        """Get list of custom theme names."""
        return list(self._custom_themes.keys())
    
    def get_theme_colors(self, name: str) -> dict:
        """Get colors for a theme by name."""
        if name in BUILTIN_THEME_COLORS:
            return BUILTIN_THEME_COLORS[name].copy()
        elif name in self._custom_themes:
            return self._custom_themes[name].copy()
        return BUILTIN_THEME_COLORS["Dark"].copy()
    
    def save_custom_theme(self, name: str, colors: dict):
        """Save a custom theme."""
        themes_dir = get_themes_dir()
        safe_name = "".join(c for c in name if c.isalnum() or c in " -_").strip()
        theme_path = os.path.join(themes_dir, f"{safe_name}.json")
        
        theme_data = {"name": name, "colors": colors}
        try:
            with open(theme_path, "w") as f:
                json.dump(theme_data, f, indent=2)
            self._custom_themes[name] = colors
        except IOError:
            pass
    
    def delete_custom_theme(self, name: str):
        """Delete a custom theme."""
        if name in self._custom_themes:
            themes_dir = get_themes_dir()
            safe_name = "".join(c for c in name if c.isalnum() or c in " -_").strip()
            theme_path = os.path.join(themes_dir, f"{safe_name}.json")
            try:
                if os.path.exists(theme_path):
                    os.remove(theme_path)
                del self._custom_themes[name]
            except (IOError, KeyError):
                pass
    
    def apply_theme(self, theme: Theme):
        """Apply a built-in theme to the application (legacy method)."""
        theme_name_map = {
            Theme.DARK: "Dark",
            Theme.LIGHT: "Light",
            Theme.AQUAMARINE: "Aquamarine",
            Theme.MIDNIGHT_BLUE: "Midnight Blue",
        }
        name = theme_name_map.get(theme, "Dark")
        self.apply_theme_by_name(name)
    
    def apply_theme_by_name(self, name: str):
        """Apply a theme by name."""
        self._current_theme_name = name
        
        name_to_enum = {
            "Dark": Theme.DARK,
            "Light": Theme.LIGHT,
            "Aquamarine": Theme.AQUAMARINE,
            "Midnight Blue": Theme.MIDNIGHT_BLUE,
        }
        self._current_theme = name_to_enum.get(name, Theme.CUSTOM)
        
        colors = self.get_theme_colors(name)
        stylesheet = generate_stylesheet_from_colors(colors)
        
        app = QApplication.instance()
        if app:
            app.setStyleSheet(stylesheet)
        
        self._save_settings()
    
    def toggle_theme(self):
        """Toggle between dark and light themes."""
        if self._current_theme_name == "Dark":
            self.apply_theme_by_name("Light")
        else:
            self.apply_theme_by_name("Dark")
    
    def get_line_number_colors(self) -> dict:
        """Get line number colors for the current theme."""
        colors = self.get_theme_colors(self._current_theme_name)
        return {
            "bg": colors.get("line_number_bg", "#1e1e1e"),
            "text": colors.get("line_number_text", "#858585"),
            "current_line": colors.get("line_number_current", "#c6c6c6"),
            "current_line_bg": colors.get("line_number_current_bg", "#282828"),
        }
