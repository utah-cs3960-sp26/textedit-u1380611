"""
Settings Dialog Module

Provides a settings dialog with theme management capabilities.
"""

import json
import os
from typing import Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QListWidget, QListWidgetItem, QPushButton, QLabel, QLineEdit,
    QGroupBox, QFormLayout, QColorDialog, QMessageBox, QScrollArea,
    QFrame, QSplitter, QSizePolicy, QFontComboBox, QSpinBox,
    QRadioButton, QButtonGroup, QTextEdit
)
from PySide6.QtGui import QColor, QPalette, QFont, QFontDatabase
from PySide6.QtCore import Qt, Signal


class ColorButton(QPushButton):
    """A button that displays and allows selecting a color."""
    
    color_changed = Signal(str)
    
    def __init__(self, color: str = "#ffffff", parent=None):
        super().__init__(parent)
        self._color = color
        self.setFixedSize(60, 30)
        self._update_style()
        self.clicked.connect(self._pick_color)
    
    @property
    def color(self) -> str:
        return self._color
    
    @color.setter
    def color(self, value: str):
        self._color = value
        self._update_style()
    
    def _update_style(self):
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {self._color};
                border: 2px solid #555;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                border: 2px solid #888;
            }}
        """)
    
    def _pick_color(self):
        color = QColorDialog.getColor(QColor(self._color), self, "Select Color")
        if color.isValid():
            self._color = color.name()
            self._update_style()
            self.color_changed.emit(self._color)


class ThemeEditorWidget(QWidget):
    """Widget for editing theme colors."""
    
    theme_modified = Signal()
    
    COLOR_FIELDS = [
        ("main_background", "Main Background"),
        ("editor_background", "Editor Background"),
        ("editor_text", "Editor Text"),
        ("selection_background", "Selection Background"),
        ("selection_text", "Selection Text"),
        ("menubar_background", "Menu Bar Background"),
        ("menubar_text", "Menu Bar Text"),
        ("menu_background", "Menu Background"),
        ("menu_text", "Menu Text"),
        ("menu_hover", "Menu Hover"),
        ("tab_background", "Tab Background"),
        ("tab_text", "Tab Text"),
        ("tab_active_background", "Active Tab Background"),
        ("tab_active_text", "Active Tab Text"),
        ("status_bar_background", "Status Bar Background"),
        ("status_bar_text", "Status Bar Text"),
        ("scrollbar_background", "Scrollbar Background"),
        ("scrollbar_handle", "Scrollbar Handle"),
        ("tree_background", "File Tree Background"),
        ("tree_text", "File Tree Text"),
        ("tree_selection", "File Tree Selection"),
        ("border_color", "Border Color"),
        ("accent_color", "Accent Color"),
        ("line_number_bg", "Line Number Background"),
        ("line_number_text", "Line Number Text"),
        ("line_number_current", "Current Line Number"),
        ("line_number_current_bg", "Current Line Background"),
    ]
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._color_buttons = {}
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        
        content = QWidget()
        content.setStyleSheet("QWidget { background: transparent; }")
        content_layout = QVBoxLayout(content)
        
        editor_group = QGroupBox("Editor Colors")
        editor_form = QFormLayout(editor_group)
        editor_fields = [
            "editor_background", "editor_text", "selection_background",
            "selection_text", "line_number_bg", "line_number_text",
            "line_number_current", "line_number_current_bg"
        ]
        for field_id, field_name in self.COLOR_FIELDS:
            if field_id in editor_fields:
                btn = ColorButton()
                btn.color_changed.connect(lambda: self.theme_modified.emit())
                self._color_buttons[field_id] = btn
                editor_form.addRow(field_name + ":", btn)
        content_layout.addWidget(editor_group)
        
        ui_group = QGroupBox("UI Colors")
        ui_form = QFormLayout(ui_group)
        ui_fields = [
            "main_background", "menubar_background", "menubar_text",
            "menu_background", "menu_text", "menu_hover",
            "tab_background", "tab_text", "tab_active_background", "tab_active_text",
            "status_bar_background", "status_bar_text",
            "scrollbar_background", "scrollbar_handle",
            "tree_background", "tree_text", "tree_selection",
            "border_color", "accent_color"
        ]
        for field_id, field_name in self.COLOR_FIELDS:
            if field_id in ui_fields:
                btn = ColorButton()
                btn.color_changed.connect(lambda: self.theme_modified.emit())
                self._color_buttons[field_id] = btn
                ui_form.addRow(field_name + ":", btn)
        content_layout.addWidget(ui_group)
        
        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)
    
    def get_colors(self) -> dict:
        """Get all color values."""
        return {field_id: btn.color for field_id, btn in self._color_buttons.items()}
    
    def set_colors(self, colors: dict):
        """Set all color values."""
        for field_id, btn in self._color_buttons.items():
            if field_id in colors:
                btn.color = colors[field_id]


class ThemeManagerWidget(QWidget):
    """Widget for managing themes in settings."""
    
    theme_applied = Signal(str)
    
    def __init__(self, theme_manager, parent=None):
        super().__init__(parent)
        self._theme_manager = theme_manager
        self._current_theme_name = None
        self._is_modified = False
        self._setup_ui()
        self._load_themes()
    
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        left_panel = QWidget()
        left_panel.setStyleSheet("QWidget { background: transparent; }")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        left_layout.addWidget(QLabel("Themes:"))
        
        self._theme_list = QListWidget()
        self._theme_list.currentItemChanged.connect(self._on_theme_selected)
        left_layout.addWidget(self._theme_list)
        
        btn_layout = QHBoxLayout()
        
        self._new_btn = QPushButton("New")
        self._new_btn.clicked.connect(self._on_new_theme)
        btn_layout.addWidget(self._new_btn)
        
        self._duplicate_btn = QPushButton("Duplicate")
        self._duplicate_btn.clicked.connect(self._on_duplicate_theme)
        btn_layout.addWidget(self._duplicate_btn)
        
        self._delete_btn = QPushButton("Delete")
        self._delete_btn.clicked.connect(self._on_delete_theme)
        btn_layout.addWidget(self._delete_btn)
        
        left_layout.addLayout(btn_layout)
        
        right_panel = QWidget()
        right_panel.setStyleSheet("QWidget { background: transparent; }")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Theme Name:"))
        self._name_edit = QLineEdit()
        self._name_edit.textChanged.connect(self._on_name_changed)
        name_layout.addWidget(self._name_edit)
        right_layout.addLayout(name_layout)
        
        self._theme_editor = ThemeEditorWidget()
        self._theme_editor.theme_modified.connect(self._on_theme_modified)
        right_layout.addWidget(self._theme_editor)
        
        action_layout = QHBoxLayout()
        
        self._save_btn = QPushButton("Save Theme")
        self._save_btn.clicked.connect(self._on_save_theme)
        action_layout.addWidget(self._save_btn)
        
        self._apply_btn = QPushButton("Apply Theme")
        self._apply_btn.clicked.connect(self._on_apply_theme)
        action_layout.addWidget(self._apply_btn)
        
        action_layout.addStretch()
        right_layout.addLayout(action_layout)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStyleSheet("QSplitter { background: transparent; }")
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([200, 400])
        
        layout.addWidget(splitter)
    
    def _load_themes(self):
        """Load all available themes into the list."""
        self._theme_list.clear()
        
        for name in self._theme_manager.get_builtin_theme_names():
            item = QListWidgetItem(f"📦 {name}")
            item.setData(Qt.ItemDataRole.UserRole, ("builtin", name))
            self._theme_list.addItem(item)
        
        for name in self._theme_manager.get_custom_theme_names():
            item = QListWidgetItem(f"✏️ {name}")
            item.setData(Qt.ItemDataRole.UserRole, ("custom", name))
            self._theme_list.addItem(item)
        
        current = self._theme_manager.current_theme_name
        for i in range(self._theme_list.count()):
            item = self._theme_list.item(i)
            theme_type, name = item.data(Qt.ItemDataRole.UserRole)
            if name == current:
                self._theme_list.setCurrentItem(item)
                break
    
    def _on_theme_selected(self, current, previous):
        """Handle theme selection change."""
        if current is None:
            return
        
        if self._is_modified and previous is not None:
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                "You have unsaved changes. Do you want to save them?",
                QMessageBox.StandardButton.Save |
                QMessageBox.StandardButton.Discard |
                QMessageBox.StandardButton.Cancel
            )
            if reply == QMessageBox.StandardButton.Save:
                self._on_save_theme()
            elif reply == QMessageBox.StandardButton.Cancel:
                self._theme_list.setCurrentItem(previous)
                return
        
        theme_type, name = current.data(Qt.ItemDataRole.UserRole)
        self._current_theme_name = name
        self._name_edit.setText(name)
        
        colors = self._theme_manager.get_theme_colors(name)
        self._theme_editor.set_colors(colors)
        
        is_builtin = theme_type == "builtin"
        self._name_edit.setReadOnly(is_builtin)
        self._delete_btn.setEnabled(not is_builtin)
        self._save_btn.setEnabled(not is_builtin)
        
        self._is_modified = False
    
    def _on_theme_modified(self):
        """Handle theme color modification."""
        self._is_modified = True
    
    def _on_name_changed(self, text):
        """Handle theme name change."""
        self._is_modified = True
    
    def _on_new_theme(self):
        """Create a new custom theme."""
        base_name = "Custom Theme"
        name = base_name
        counter = 1
        existing = self._theme_manager.get_custom_theme_names()
        while name in existing:
            counter += 1
            name = f"{base_name} {counter}"
        
        default_colors = self._theme_manager.get_theme_colors("Dark")
        self._theme_manager.save_custom_theme(name, default_colors)
        self._load_themes()
        
        for i in range(self._theme_list.count()):
            item = self._theme_list.item(i)
            theme_type, theme_name = item.data(Qt.ItemDataRole.UserRole)
            if theme_name == name:
                self._theme_list.setCurrentItem(item)
                break
    
    def _on_duplicate_theme(self):
        """Duplicate the current theme."""
        if self._current_theme_name is None:
            return
        
        base_name = f"{self._current_theme_name} Copy"
        name = base_name
        counter = 1
        existing = (
            self._theme_manager.get_builtin_theme_names() +
            self._theme_manager.get_custom_theme_names()
        )
        while name in existing:
            counter += 1
            name = f"{base_name} {counter}"
        
        colors = self._theme_editor.get_colors()
        self._theme_manager.save_custom_theme(name, colors)
        self._load_themes()
        
        for i in range(self._theme_list.count()):
            item = self._theme_list.item(i)
            theme_type, theme_name = item.data(Qt.ItemDataRole.UserRole)
            if theme_name == name:
                self._theme_list.setCurrentItem(item)
                break
    
    def _on_delete_theme(self):
        """Delete the current custom theme."""
        if self._current_theme_name is None:
            return
        
        current = self._theme_list.currentItem()
        if current is None:
            return
        
        theme_type, name = current.data(Qt.ItemDataRole.UserRole)
        if theme_type == "builtin":
            QMessageBox.warning(self, "Cannot Delete", "Built-in themes cannot be deleted.")
            return
        
        reply = QMessageBox.question(
            self, "Delete Theme",
            f"Are you sure you want to delete '{name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self._theme_manager.delete_custom_theme(name)
            self._is_modified = False
            self._load_themes()
    
    def _on_save_theme(self):
        """Save the current theme."""
        current = self._theme_list.currentItem()
        if current is None:
            return
        
        theme_type, old_name = current.data(Qt.ItemDataRole.UserRole)
        if theme_type == "builtin":
            QMessageBox.information(
                self, "Built-in Theme",
                "Built-in themes cannot be modified. Use 'Duplicate' to create an editable copy."
            )
            return
        
        new_name = self._name_edit.text().strip()
        if not new_name:
            QMessageBox.warning(self, "Invalid Name", "Theme name cannot be empty.")
            return
        
        colors = self._theme_editor.get_colors()
        
        if old_name != new_name:
            self._theme_manager.delete_custom_theme(old_name)
        
        self._theme_manager.save_custom_theme(new_name, colors)
        self._current_theme_name = new_name
        self._is_modified = False
        self._load_themes()
        
        for i in range(self._theme_list.count()):
            item = self._theme_list.item(i)
            theme_type, theme_name = item.data(Qt.ItemDataRole.UserRole)
            if theme_name == new_name:
                self._theme_list.setCurrentItem(item)
                break
    
    def _on_apply_theme(self):
        """Apply the currently selected theme."""
        if self._is_modified:
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                "Save changes before applying?",
                QMessageBox.StandardButton.Save |
                QMessageBox.StandardButton.No |
                QMessageBox.StandardButton.Cancel
            )
            if reply == QMessageBox.StandardButton.Save:
                self._on_save_theme()
            elif reply == QMessageBox.StandardButton.Cancel:
                return
        
        current = self._theme_list.currentItem()
        if current is None:
            return
        
        theme_type, name = current.data(Qt.ItemDataRole.UserRole)
        self.theme_applied.emit(name)


class FontManagerWidget(QWidget):
    """Widget for managing fonts in settings."""
    
    font_apply_requested = Signal(QFont, bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._editor_bg = "#1e1e1e"
        self._editor_text = "#d4d4d4"
        self._setup_ui()
    
    def set_theme_colors(self, editor_bg: str, editor_text: str):
        """Set the theme colors for the preview."""
        self._editor_bg = editor_bg
        self._editor_text = editor_text
        self._apply_theme_style()
    
    def _apply_theme_style(self):
        """Apply theme colors to widgets."""
        self._preview_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {self._editor_bg};
                color: {self._editor_text};
                border: 1px solid {self._editor_text}40;
                border-radius: 4px;
            }}
        """)
        
        self.setStyleSheet(f"""
            QGroupBox {{
                color: {self._editor_text};
            }}
            QGroupBox::title {{
                color: {self._editor_text};
            }}
            QRadioButton {{
                color: {self._editor_text};
            }}
            QLabel {{
                color: {self._editor_text};
            }}
        """)
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        font_group = QGroupBox("Font Selection")
        font_layout = QFormLayout(font_group)
        
        self._font_combo = QFontComboBox()
        self._font_combo.setCurrentFont(QFont("Monospace"))
        self._font_combo.currentFontChanged.connect(self._update_preview)
        font_layout.addRow("Font Family:", self._font_combo)
        
        self._size_spin = QSpinBox()
        self._size_spin.setRange(6, 72)
        self._size_spin.setValue(12)
        self._size_spin.valueChanged.connect(self._update_preview)
        font_layout.addRow("Font Size:", self._size_spin)
        
        layout.addWidget(font_group)
        
        preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout(preview_group)
        
        self._preview_text = QTextEdit()
        self._preview_text.setPlainText(
            "The quick brown fox jumps over the lazy dog.\n"
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ\n"
            "abcdefghijklmnopqrstuvwxyz\n"
            "0123456789 !@#$%^&*()_+-=[]{}|;':\",./<>?"
        )
        self._preview_text.setMinimumHeight(100)
        self._preview_text.setMaximumHeight(150)
        self._preview_text.setReadOnly(True)
        self._apply_theme_style()
        preview_layout.addWidget(self._preview_text)
        
        layout.addWidget(preview_group)
        
        apply_group = QGroupBox("Apply To")
        apply_layout = QVBoxLayout(apply_group)
        
        self._apply_group = QButtonGroup(self)
        
        self._apply_all_radio = QRadioButton("Apply to all text in document")
        self._apply_all_radio.setChecked(True)
        self._apply_group.addButton(self._apply_all_radio)
        apply_layout.addWidget(self._apply_all_radio)
        
        self._apply_selection_radio = QRadioButton("Apply to selected text only")
        self._apply_group.addButton(self._apply_selection_radio)
        apply_layout.addWidget(self._apply_selection_radio)
        
        layout.addWidget(apply_group)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self._apply_btn = QPushButton("Apply Font")
        self._apply_btn.clicked.connect(self._on_apply_font)
        btn_layout.addWidget(self._apply_btn)
        
        layout.addLayout(btn_layout)
        layout.addStretch()
        
        self._update_preview()
    
    def _update_preview(self):
        """Update the preview text with the selected font."""
        font = self._font_combo.currentFont()
        font.setPointSize(self._size_spin.value())
        self._preview_text.setFont(font)
    
    def _on_apply_font(self):
        """Emit signal to apply font."""
        font = self._font_combo.currentFont()
        font.setPointSize(self._size_spin.value())
        apply_to_selection = self._apply_selection_radio.isChecked()
        self.font_apply_requested.emit(font, apply_to_selection)
    
    def get_current_font(self) -> QFont:
        """Get the currently selected font."""
        font = self._font_combo.currentFont()
        font.setPointSize(self._size_spin.value())
        return font
    
    def is_selection_mode(self) -> bool:
        """Check if applying to selection only."""
        return self._apply_selection_radio.isChecked()


class SettingsDialog(QDialog):
    """Settings dialog with theme management."""
    
    theme_changed = Signal(str)
    
    def __init__(self, theme_manager, parent=None):
        super().__init__(parent)
        self._theme_manager = theme_manager
        self._setup_ui()
    
    def _setup_ui(self):
        self.setWindowTitle("Theme Manager")
        self.setMinimumSize(700, 500)
        self.resize(800, 600)
        
        layout = QVBoxLayout(self)
        
        theme_widget = ThemeManagerWidget(self._theme_manager)
        theme_widget.theme_applied.connect(self._on_theme_applied)
        layout.addWidget(theme_widget)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
    
    def _on_theme_applied(self, theme_name: str):
        """Handle theme application."""
        self.theme_changed.emit(theme_name)


class FontManagerDialog(QDialog):
    """Dialog for font management."""
    
    font_apply_requested = Signal(QFont, bool)
    
    def __init__(self, theme_manager, parent=None):
        super().__init__(parent)
        self._theme_manager = theme_manager
        self._setup_ui()
        self._apply_theme_colors()
    
    def _setup_ui(self):
        self.setWindowTitle("Font Manager")
        self.setMinimumSize(400, 450)
        self.resize(450, 500)
        
        layout = QVBoxLayout(self)
        
        self._font_widget = FontManagerWidget()
        self._font_widget.font_apply_requested.connect(self._on_font_apply)
        layout.addWidget(self._font_widget)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
    
    def _apply_theme_colors(self):
        """Apply theme colors to the font widget."""
        colors = self._theme_manager.get_theme_colors(
            self._theme_manager.current_theme_name
        )
        self._font_widget.set_theme_colors(
            colors.get("editor_background", "#1e1e1e"),
            colors.get("editor_text", "#d4d4d4")
        )
    
    def _on_font_apply(self, font: QFont, selection_only: bool):
        """Handle font application request."""
        self.font_apply_requested.emit(font, selection_only)
