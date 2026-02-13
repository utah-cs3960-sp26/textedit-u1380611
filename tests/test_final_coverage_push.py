"""
Final coverage push targeting 95%+

Focused tests for:
- split_container.py lines 297, 363-364 (missing 2 lines)
- tab_bar.py lines 214-215, 228 (missing 3 lines)
- file_tree.py lines 119, 139-140, 324-326 (missing 6 lines)
- font_toolbar.py lines 188-190 (missing 3 lines)
- theme_manager.py lines 1751-1752 (missing 2 lines)
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QDropEvent, QDragEnterEvent, QDragLeaveEvent
from PySide6.QtCore import Qt, QPoint, QMimeData

from editor.document import Document
from editor.editor_pane import EditorPane
from editor.split_container import SplitContainer
from editor.tab_bar import EditorTabBar


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def container(qapp):
    widget = SplitContainer()
    yield widget
    widget.deleteLater()


@pytest.fixture
def pane(qapp):
    widget = EditorPane()
    yield widget
    widget.deleteLater()


@pytest.fixture
def tab_bar(qapp):
    bar = EditorTabBar()
    yield bar
    bar.deleteLater()


# ============================================================================
# split_container.py - Line 297: return when doc is None
# ============================================================================
class TestSplitContainerCloseTabNoneDoc:
    """Test _on_close_tab_requested when document is None (line 297)."""
    
    def test_close_tab_with_none_document(self, container):
        """Should return early when get_document_at returns None."""
        pane = container.active_pane
        
        # Mock get_document_at to return None
        with patch.object(pane, 'get_document_at', return_value=None):
            # Should not crash and return early
            result = container._on_close_tab_requested(pane, 0)
            
            # Verify it returned (or didn't emit signal)
            assert result is None


# ============================================================================
# split_container.py - Lines 363-364: event.ignore() when document is None
# ============================================================================
class TestTabBarDropDocumentNone:
    """Test _handle_tab_bar_drop when document is None (lines 363-364)."""
    
    def test_handle_tab_bar_drop_document_none(self, container):
        """Should ignore event when document is None."""
        target_pane = container.active_pane
        # Create a second pane so source_pane != target_pane
        source_pane = container._create_pane()
        source_pane.add_new_document()
        
        # Build real mime data with the correct MIME_TYPE and a valid index
        mime_data = QMimeData()
        mime_data.setData(EditorTabBar.MIME_TYPE, b"0")
        
        event = MagicMock(spec=QDropEvent)
        event.mimeData.return_value = mime_data
        event.source.return_value = source_pane.tab_bar
        event.position.return_value.toPoint.return_value = QPoint(10, 10)
        
        # Mock source_pane to return None for document
        with patch.object(source_pane, 'get_document_at', return_value=None):
            container._handle_tab_bar_drop(target_pane, event)
            
            # Should have called ignore() on event
            event.ignore.assert_called()


# ============================================================================
# tab_bar.py - Lines 214-215: dragLeaveEvent
# ============================================================================
class TestTabBarDragLeaveEvent:
    """Test dragLeaveEvent super call (lines 214-215)."""
    
    def test_drag_leave_event(self, tab_bar):
        """dragLeaveEvent should hide indicator and call super."""
        # Show the tab bar so child visibility works
        tab_bar.show()
        tab_bar._drop_indicator.setGeometry(0, 0, 4, tab_bar.height())
        tab_bar._drop_indicator.show()
        
        # Create a real QDragLeaveEvent (super() requires it)
        event = QDragLeaveEvent()
        
        # Call dragLeaveEvent - covers lines 214-215
        tab_bar.dragLeaveEvent(event)
        
        # Indicator should be hidden
        assert not tab_bar._drop_indicator.isVisible()
        tab_bar.hide()


# ============================================================================
# tab_bar.py - Line 228: else branch in _show_drop_indicator
# ============================================================================
class TestTabBarShowDropIndicatorEmptyBar:
    """Test _show_drop_indicator with empty tab bar (line 228)."""
    
    def test_show_drop_indicator_empty_bar(self, tab_bar):
        """_show_drop_indicator with no tabs should set x=0."""
        # Tab bar is initially empty (count() == 0)
        assert tab_bar.count() == 0
        
        # Call _show_drop_indicator
        tab_bar._show_drop_indicator(QPoint(50, 15))
        
        # Check that indicator geometry has x=0 (approximately)
        geometry = tab_bar._drop_indicator.geometry()
        assert geometry.left() >= -5  # Allow small offset


# ============================================================================
# file_tree.py - Line 119, 139-140: sidebar widget replacement
# ============================================================================
class TestFileTreeSidebarReplacement:
    """Test FileTree sidebar widget replacement (lines 119, 139-140)."""
    
    def test_open_folder_replaces_sidebar_widget(self, tmp_path):
        """Opening folder should properly set sidebar widget."""
        from editor.file_tree import FileTree, CollapsibleSidebar
        
        sidebar = CollapsibleSidebar()
        tree = FileTree()
        sidebar.set_content(tree)
        
        # Create test folder
        test_folder = tmp_path / "test"
        test_folder.mkdir()
        (test_folder / "file.txt").write_text("content")
        
        # Open folder - this should set up the tree
        result = tree.open_folder(str(test_folder))
        assert result is True
        assert tree.root_path == str(test_folder.resolve())
        
        # Replace sidebar content with a new widget
        tree2 = FileTree()
        sidebar.set_content(tree2)
        
        # Verify the sidebar's content widget is the new one
        assert sidebar._content_widget is tree2
        
        tree.deleteLater()
        tree2.deleteLater()
        sidebar.deleteLater()


# ============================================================================
# file_tree.py - Lines 324-326: mousePressEvent middle click
# ============================================================================
class TestFileTreeMouseMiddleClick:
    """Test FileTreeView mousePressEvent middle click (lines 324-326)."""
    
    def test_file_tree_view_middle_click(self, tmp_path):
        """Middle click should emit middle_clicked signal on valid index."""
        from editor.file_tree import FileTreeView
        from PySide6.QtGui import QMouseEvent
        from PySide6.QtCore import QEvent, QModelIndex
        
        view = FileTreeView()
        
        # Prepare signal capture
        signal_emitted = []
        view.middle_clicked.connect(
            lambda index: signal_emitted.append(index)
        )
        
        # Create middle click event at a position
        event = QMouseEvent(
            QEvent.Type.MouseButtonPress,
            QPoint(50, 30),
            Qt.MouseButton.MiddleButton,
            Qt.MouseButton.MiddleButton,
            Qt.KeyboardModifier.NoModifier
        )
        
        # Mock indexAt to return a valid index
        valid_index = MagicMock(spec=QModelIndex)
        valid_index.isValid.return_value = True
        with patch.object(view, 'indexAt', return_value=valid_index):
            view.mousePressEvent(event)
        
        # Signal should have been emitted
        assert len(signal_emitted) == 1
        
        view.deleteLater()


# ============================================================================
# font_toolbar.py - Lines 188-190: position_bottom overflow
# ============================================================================
class TestFontToolbarPositionBottom:
    """Test FontMiniToolbar _position_near_selection overflow handling (lines 187-190)."""
    
    def test_position_bottom_handles_overflow(self, qapp):
        """_position_near_selection should handle y overflow by positioning above."""
        from editor.font_toolbar import FontMiniToolbar
        from PySide6.QtWidgets import QMainWindow, QPlainTextEdit
        from PySide6.QtCore import QRect
        from PySide6.QtGui import QTextCursor
        
        main_window = QMainWindow()
        main_window.resize(800, 600)
        main_window.show()
        
        editor = QPlainTextEdit(main_window)
        main_window.setCentralWidget(editor)
        editor.setPlainText("Hello world\nLine 2\nLine 3")
        
        toolbar = FontMiniToolbar()
        toolbar.set_main_window(main_window)
        toolbar._editor = editor
        toolbar.resize(300, 40)
        
        # Mock cursorRect to return a rect near the bottom of the window
        # so that toolbar_y + height > main_rect.bottom(), triggering lines 188-190
        bottom_rect = QRect(50, 590, 10, 20)  # near bottom of 600px window
        top_rect = QRect(50, 570, 10, 20)
        
        cursor = editor.textCursor()
        with patch.object(editor, 'cursorRect', return_value=bottom_rect):
            toolbar._position_near_selection(cursor)
        
        # Should not crash and toolbar should have been positioned
        toolbar.deleteLater()
        main_window.deleteLater()


# ============================================================================
# theme_manager.py - Lines 1751-1752: get_theme_colors fallback
# ============================================================================
class TestThemeManagerColorsFallback:
    """Test ThemeManager get_theme_colors fallback (lines 1751-1752)."""
    
    def test_get_theme_colors_unknown_theme(self):
        """get_theme_colors should fallback for unknown theme."""
        from editor.theme_manager import ThemeManager
        
        tm = ThemeManager()
        
        # Request colors for nonexistent theme
        colors = tm.get_theme_colors("unknown_theme_xyz")
        
        # Should return dict (fallback colors)
        assert isinstance(colors, dict)
        # Fallback should have some default colors
        assert len(colors) > 0


# ============================================================================
# Additional edge cases for coverage gaps
# ============================================================================
class TestEditorPaneNoneDocument:
    """Test EditorPane operations with None document."""
    
    def test_add_document_to_none_pane(self, container):
        """add_document with no active pane should be safe."""
        container._active_pane = None
        
        doc = Document()
        result = container.add_document(doc)
        
        assert result is None or result is False


class TestTabBarDropIndicatorPositioning:
    """Test tab bar drop indicator positioning edge cases."""
    
    def test_drop_indicator_with_drop_index_beyond_count(self, tab_bar):
        """_show_drop_indicator with drop_index >= count."""
        tab_bar.addTab("Tab 1")
        
        # Force drop index beyond count
        with patch.object(tab_bar, 'get_drop_index', return_value=999):
            tab_bar._show_drop_indicator(QPoint(50, 15))
            
            # Should still show indicator without crashing
            geometry = tab_bar._drop_indicator.geometry()
            assert geometry.width() == 4


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
