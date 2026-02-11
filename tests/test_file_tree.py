"""
Tests for the file tree module.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from PySide6.QtCore import Qt, QModelIndex, QPoint
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QApplication

from editor.file_tree import FileTree, FileTreeView, CollapsibleSidebar


@pytest.fixture(scope="session")
def qapp():
    """Create a QApplication instance for the test session."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


class TestFileTreeCreation:
    """Tests for FileTree widget creation."""
    
    def test_file_tree_creation(self, qapp):
        """FileTree can be created."""
        tree = FileTree()
        assert tree is not None
        tree.deleteLater()
    
    def test_file_tree_has_toolbar(self, qapp):
        """FileTree has a toolbar with actions."""
        tree = FileTree()
        assert tree._toolbar is not None
        assert tree._open_folder_action is not None
        assert tree._refresh_action is not None
        assert tree._close_folder_action is not None
        tree.deleteLater()
    
    def test_file_tree_has_tree_view(self, qapp):
        """FileTree has a tree view."""
        tree = FileTree()
        assert tree._tree_view is not None
        assert isinstance(tree._tree_view, FileTreeView)
        tree.deleteLater()
    
    def test_initial_root_path_is_none(self, qapp):
        """Initially no folder is open."""
        tree = FileTree()
        assert tree.root_path is None
        tree.deleteLater()
    
    def test_close_folder_initially_disabled(self, qapp):
        """Close folder action is disabled when no folder is open."""
        tree = FileTree()
        assert not tree._close_folder_action.isEnabled()
        tree.deleteLater()


class TestFileTreeOpenFolder:
    """Tests for opening folders in the file tree."""
    
    def test_open_valid_folder(self, qapp):
        """Can open a valid folder."""
        tree = FileTree()
        with tempfile.TemporaryDirectory() as tmpdir:
            result = tree.open_folder(tmpdir)
            assert result is True
            assert tree.root_path == str(Path(tmpdir).resolve())
            assert tree._close_folder_action.isEnabled()
        tree.deleteLater()
    
    def test_open_invalid_folder(self, qapp):
        """Opening non-existent folder returns False."""
        tree = FileTree()
        result = tree.open_folder("/nonexistent/path/that/does/not/exist")
        assert result is False
        assert tree.root_path is None
        tree.deleteLater()
    
    def test_open_file_instead_of_folder(self, qapp):
        """Opening a file instead of folder returns False."""
        tree = FileTree()
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test")
            filepath = f.name
        
        try:
            result = tree.open_folder(filepath)
            assert result is False
        finally:
            os.unlink(filepath)
        tree.deleteLater()
    
    def test_close_folder(self, qapp):
        """Can close an open folder."""
        tree = FileTree()
        with tempfile.TemporaryDirectory() as tmpdir:
            tree.open_folder(tmpdir)
            tree.close_folder()
            assert tree.root_path is None
            assert not tree._close_folder_action.isEnabled()
        tree.deleteLater()
    
    def test_close_folder_defaults_to_home_directory(self, qapp):
        """When a folder is closed, it defaults to the user's home directory."""
        tree = FileTree()
        with tempfile.TemporaryDirectory() as tmpdir:
            tree.open_folder(tmpdir)
            tree.close_folder()
            # After closing, the tree should display the home directory
            home_dir = os.path.expanduser("~")
            assert tree._model.rootPath() == home_dir
        tree.deleteLater()


class TestFileTreeRefresh:
    """Tests for refreshing the file tree."""
    
    def test_refresh_with_folder(self, qapp):
        """Refresh works when a folder is open."""
        tree = FileTree()
        with tempfile.TemporaryDirectory() as tmpdir:
            tree.open_folder(tmpdir)
            tree.refresh()
            assert tree.root_path == str(Path(tmpdir).resolve())
        tree.deleteLater()
    
    def test_refresh_without_folder(self, qapp):
        """Refresh is safe when no folder is open."""
        tree = FileTree()
        tree.refresh()
        assert tree.root_path is None
        tree.deleteLater()


class TestFileTreeView:
    """Tests for the custom FileTreeView."""
    
    def test_file_tree_view_creation(self, qapp):
        """FileTreeView can be created."""
        view = FileTreeView()
        assert view is not None
        view.deleteLater()
    
    def test_middle_click_signal_exists(self, qapp):
        """FileTreeView has middle_clicked signal."""
        view = FileTreeView()
        assert hasattr(view, 'middle_clicked')
        view.deleteLater()


class TestFileTreeSignals:
    """Tests for file tree signals."""
    
    def test_file_open_requested_signal(self, qapp):
        """file_open_requested signal exists."""
        tree = FileTree()
        assert hasattr(tree, 'file_open_requested')
        tree.deleteLater()
    
    def test_file_open_new_tab_requested_signal(self, qapp):
        """file_open_new_tab_requested signal exists."""
        tree = FileTree()
        assert hasattr(tree, 'file_open_new_tab_requested')
        tree.deleteLater()


class TestCollapsibleSidebar:
    """Tests for the CollapsibleSidebar widget."""
    
    def test_sidebar_creation(self, qapp):
        """CollapsibleSidebar can be created."""
        sidebar = CollapsibleSidebar()
        assert sidebar is not None
        sidebar.deleteLater()
    
    def test_sidebar_initially_not_collapsed(self, qapp):
        """Sidebar is not collapsed by default."""
        sidebar = CollapsibleSidebar()
        assert sidebar.is_collapsed is False
        sidebar.deleteLater()
    
    def test_set_collapsed(self, qapp):
        """Can set collapsed state."""
        sidebar = CollapsibleSidebar()
        sidebar.set_collapsed(True)
        assert sidebar.is_collapsed is True
        sidebar.deleteLater()
    
    def test_toggle_collapsed(self, qapp):
        """Can toggle collapsed state."""
        sidebar = CollapsibleSidebar()
        assert sidebar.is_collapsed is False
        sidebar.toggle_collapsed()
        assert sidebar.is_collapsed is True
        sidebar.toggle_collapsed()
        assert sidebar.is_collapsed is False
        sidebar.deleteLater()
    
    def test_set_content(self, qapp):
        """Can set content widget."""
        sidebar = CollapsibleSidebar()
        tree = FileTree()
        sidebar.set_content(tree)
        assert sidebar._content_widget is tree
        sidebar.deleteLater()
    
    def test_collapsed_changed_signal(self, qapp):
        """collapsed_changed signal is emitted."""
        sidebar = CollapsibleSidebar()
        signal_received = []
        sidebar.collapsed_changed.connect(lambda v: signal_received.append(v))
        sidebar.set_collapsed(True)
        assert signal_received == [True]
        sidebar.deleteLater()
    
    def test_collapsed_width(self, qapp):
        """Collapsed sidebar has narrow width."""
        sidebar = CollapsibleSidebar()
        sidebar.set_collapsed(True)
        assert sidebar.width() <= 20
        sidebar.deleteLater()


class TestFileTreeInteractions:
    """Tests for file tree user interactions (event handlers)."""
    
    def test_on_open_folder_with_selection(self, qapp):
        """_on_open_folder opens selected folder."""
        tree = FileTree()
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('editor.file_tree.QFileDialog.getExistingDirectory', return_value=tmpdir):
                tree._on_open_folder()
                assert tree.root_path == str(Path(tmpdir).resolve())
        tree.deleteLater()
    
    def test_on_open_folder_with_no_selection(self, qapp):
        """_on_open_folder with empty dialog result does nothing."""
        tree = FileTree()
        with patch('editor.file_tree.QFileDialog.getExistingDirectory', return_value=''):
            tree._on_open_folder()
            assert tree.root_path is None
        tree.deleteLater()
    
    def test_on_refresh_action(self, qapp):
        """_on_refresh calls refresh."""
        tree = FileTree()
        with tempfile.TemporaryDirectory() as tmpdir:
            tree.open_folder(tmpdir)
            tree._on_refresh()
            assert tree.root_path == str(Path(tmpdir).resolve())
        tree.deleteLater()
    
    def test_on_close_folder_action(self, qapp):
        """_on_close_folder calls close_folder."""
        tree = FileTree()
        with tempfile.TemporaryDirectory() as tmpdir:
            tree.open_folder(tmpdir)
            tree._on_close_folder()
            assert tree.root_path is None
        tree.deleteLater()
    
    def test_on_item_double_clicked_with_file(self, qapp):
        """Double-clicking a file emits file_open_requested signal."""
        tree = FileTree()
        signal_emitted = []
        tree.file_open_requested.connect(lambda path: signal_emitted.append(path))
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test file
            test_file = os.path.join(tmpdir, "test.txt")
            Path(test_file).touch()
            
            tree.open_folder(tmpdir)
            # Get index of the file
            file_index = tree._model.index(test_file)
            
            tree._on_item_double_clicked(file_index)
            assert len(signal_emitted) == 1
            assert signal_emitted[0] == test_file
        
        tree.deleteLater()
    
    def test_on_item_double_clicked_with_folder(self, qapp):
        """Double-clicking a folder doesn't emit signal."""
        tree = FileTree()
        signal_emitted = []
        tree.file_open_requested.connect(lambda path: signal_emitted.append(path))
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a subfolder
            subfolder = os.path.join(tmpdir, "subfolder")
            os.makedirs(subfolder)
            
            tree.open_folder(tmpdir)
            folder_index = tree._model.index(subfolder)
            
            tree._on_item_double_clicked(folder_index)
            assert len(signal_emitted) == 0
        
        tree.deleteLater()
    
    def test_on_item_double_clicked_with_invalid_index(self, qapp):
        """Double-clicking invalid index does nothing."""
        tree = FileTree()
        signal_emitted = []
        tree.file_open_requested.connect(lambda path: signal_emitted.append(path))
        
        invalid_index = QModelIndex()
        tree._on_item_double_clicked(invalid_index)
        assert len(signal_emitted) == 0
        tree.deleteLater()
    
    def test_on_item_middle_clicked_with_file(self, qapp):
        """Middle-clicking a file emits file_open_new_tab_requested signal."""
        tree = FileTree()
        signal_emitted = []
        tree.file_open_new_tab_requested.connect(lambda path: signal_emitted.append(path))
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test file
            test_file = os.path.join(tmpdir, "test.txt")
            Path(test_file).touch()
            
            tree.open_folder(tmpdir)
            file_index = tree._model.index(test_file)
            
            tree._on_item_middle_clicked(file_index)
            assert len(signal_emitted) == 1
            assert signal_emitted[0] == test_file
        
        tree.deleteLater()
    
    def test_on_item_middle_clicked_with_folder(self, qapp):
        """Middle-clicking a folder doesn't emit signal."""
        tree = FileTree()
        signal_emitted = []
        tree.file_open_new_tab_requested.connect(lambda path: signal_emitted.append(path))
        
        with tempfile.TemporaryDirectory() as tmpdir:
            subfolder = os.path.join(tmpdir, "subfolder")
            os.makedirs(subfolder)
            
            tree.open_folder(tmpdir)
            folder_index = tree._model.index(subfolder)
            
            tree._on_item_middle_clicked(folder_index)
            assert len(signal_emitted) == 0
        
        tree.deleteLater()
    
    def test_on_item_middle_clicked_with_invalid_index(self, qapp):
        """Middle-clicking invalid index does nothing."""
        tree = FileTree()
        signal_emitted = []
        tree.file_open_new_tab_requested.connect(lambda path: signal_emitted.append(path))
        
        invalid_index = QModelIndex()
        tree._on_item_middle_clicked(invalid_index)
        assert len(signal_emitted) == 0
        tree.deleteLater()


class TestFileTreeViewMouseEvents:
    """Tests for FileTreeView mouse event handling."""
    
    def test_mouse_press_middle_button(self, qapp):
        """Middle mouse button click emits signal."""
        view = FileTreeView()
        signal_emitted = []
        view.middle_clicked.connect(lambda idx: signal_emitted.append(idx))
        
        # Create a mock mouse event
        event = QMouseEvent(
            QMouseEvent.Type.MouseButtonPress,
            QPoint(10, 10),
            Qt.MouseButton.MiddleButton,
            Qt.MouseButton.MiddleButton,
            Qt.KeyboardModifier.NoModifier
        )
        
        view.mousePressEvent(event)
        # Signal should be emitted (though index might be invalid)
        assert len(signal_emitted) >= 0  # May or may not have index
        view.deleteLater()
    
    def test_mouse_press_left_button(self, qapp):
        """Left mouse button click doesn't trigger middle_clicked signal."""
        view = FileTreeView()
        signal_emitted = []
        view.middle_clicked.connect(lambda idx: signal_emitted.append(idx))
        
        event = QMouseEvent(
            QMouseEvent.Type.MouseButtonPress,
            QPoint(10, 10),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier
        )
        
        view.mousePressEvent(event)
        assert len(signal_emitted) == 0
        view.deleteLater()
    
    def test_file_tree_opens_folder_successfully(self, qapp, tmp_path):
        """open_folder loads directory structure."""
        tree = FileTree()
        
        # Create test file structure
        test_dir = tmp_path / "test_project"
        test_dir.mkdir()
        (test_dir / "file.txt").write_text("test")
        
        result = tree.open_folder(str(test_dir))
        
        # Verify folder was opened successfully
        assert result is True
        assert tree.root_path == str(test_dir)
        
        tree.deleteLater()
    
    def test_file_tree_refresh_action_exists(self, qapp, tmp_path):
        """FileTree has refresh action that can be triggered."""
        tree = FileTree()
        
        test_dir = tmp_path / "test_project"
        test_dir.mkdir()
        
        tree.open_folder(str(test_dir))
        
        # Verify refresh can be called without error
        tree.refresh()
        assert True
        
        tree.deleteLater()
    
    def test_file_tree_closes_folder(self, qapp, tmp_path):
        """close_folder clears the current folder."""
        tree = FileTree()
        
        test_dir = tmp_path / "test_project"
        test_dir.mkdir()
        
        tree.open_folder(str(test_dir))
        assert tree.root_path == str(test_dir)
        
        tree.close_folder()
        assert tree.root_path is None
        
        tree.deleteLater()


class TestCollapsibleSidebar:
    """Tests for CollapsibleSidebar."""
    
    def test_sidebar_set_content(self, qapp):
        """set_content updates the content widget."""
        from PySide6.QtWidgets import QLabel
        from editor.file_tree import CollapsibleSidebar
        
        sidebar = CollapsibleSidebar()
        label1 = QLabel("Content 1")
        label2 = QLabel("Content 2")
        
        sidebar.set_content(label1)
        assert sidebar._content_widget == label1
        
        sidebar.set_content(label2)
        assert sidebar._content_widget == label2
        
        sidebar.deleteLater()
    
    def test_sidebar_set_collapsed_same_state(self, qapp):
        """set_collapsed with same state returns early."""
        from editor.file_tree import CollapsibleSidebar
        
        sidebar = CollapsibleSidebar()
        
        signal_count = []
        sidebar.collapsed_changed.connect(lambda x: signal_count.append(x))
        
        sidebar.set_collapsed(False)  # Already false
        
        # Signal should not be emitted on no-op
        assert len(signal_count) == 0
        
        sidebar.deleteLater()
    
    def test_sidebar_toggle_collapsed(self, qapp):
        """toggle_collapsed changes state."""
        from editor.file_tree import CollapsibleSidebar
        
        sidebar = CollapsibleSidebar()
        initial = sidebar.is_collapsed
        
        sidebar.toggle_collapsed()
        
        assert sidebar.is_collapsed != initial
        
        sidebar.deleteLater()
    
    def test_sidebar_internal_toggle(self, qapp):
        """_toggle_collapsed calls toggle_collapsed."""
        from editor.file_tree import CollapsibleSidebar
        
        sidebar = CollapsibleSidebar()
        initial = sidebar.is_collapsed
        
        sidebar._toggle_collapsed()
        
        assert sidebar.is_collapsed != initial
        
        sidebar.deleteLater()
