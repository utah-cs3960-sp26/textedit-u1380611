"""
Test to specifically cover line 350 in find_replace.py
"""

import pytest
from PySide6.QtWidgets import QApplication, QPlainTextEdit
from PySide6.QtGui import QTextCursor

from editor.find_replace import FindReplaceDialog


@pytest.fixture(scope="session")
def qapp():
    """Create a QApplication instance for the test session."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def editor(qapp):
    """Create a fresh QPlainTextEdit."""
    widget = QPlainTextEdit()
    yield widget
    widget.deleteLater()


class TestLine350Coverage:
    """Tests specifically for line 350 coverage."""
    
    def test_replace_current_index_wraps_on_boundary(self, editor):
        """Test that index wraps to 0 when >= len(matches) after replace."""
        # Setup: 3 identical words
        editor.setPlainText("cat cat cat")
        
        dialog = FindReplaceDialog(editor)
        dialog._find_edit.setText("cat")
        dialog._replace_edit.setText("dog")
        dialog._do_deferred_search()
        
        # Verify we have 3 matches
        assert len(dialog._matches) == 3
        
        # Set current to last match (index 2)
        dialog._current_match_index = 2
        dialog._goto_current_match()
        
        # Verify selection is at last match
        cursor = editor.textCursor()
        assert cursor.hasSelection()
        
        # Now replace - this should:
        # 1. Replace "cat" with "dog" at position of last match
        # 2. Re-search and find only 2 "cat" remaining  
        # 3. Have current_match_index = 2, but len(matches) = 2
        # 4. So line 349 condition is TRUE (2 >= 2)
        # 5. Execute line 350: index wraps to 0
        
        dialog._replace_current()
        
        # After replace, should have wrapped to index 0
        assert dialog._current_match_index == 0
        assert "dog" in editor.toPlainText()
        
        dialog.deleteLater()
    
    def test_replace_exact_boundary_condition(self, editor):
        """Test exact boundary: index == len(matches) after search."""
        # Start with 2 identical words
        editor.setPlainText("cat cat")
        
        dialog = FindReplaceDialog(editor)
        dialog._find_edit.setText("cat")
        dialog._replace_edit.setText("dog")
        dialog._do_deferred_search()
        
        assert len(dialog._matches) == 2
        
        # Set to last match
        dialog._current_match_index = 1
        dialog._goto_current_match()
        
        # Replace the last occurrence
        dialog._replace_current()
        
        # Now we have only 1 "cat" match, and current_match_index = 1
        # 1 >= 1 is TRUE, so should wrap
        assert dialog._current_match_index == 0
        
        dialog.deleteLater()
