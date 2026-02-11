"""
Pytest configuration and shared fixtures.
"""

import sys
from pathlib import Path
import pytest
from unittest.mock import patch

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(autouse=True)
def mock_drag_exec():
    """Automatically mock QDrag.exec() to prevent blocking during tests."""
    with patch('editor.tab_bar.QDrag') as mock_drag_class:
        mock_drag_instance = mock_drag_class.return_value
        mock_drag_instance.exec.return_value = 0
        yield mock_drag_class


@pytest.fixture(autouse=True)
def cleanup_grabs():
    """Automatically release mouse and keyboard grabs after each test."""
    yield
    # After test cleanup
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance()
    if app:
        try:
            # Release any active grabs
            widget = app.mouseGrabber()
            if widget:
                widget.releaseMouse()
            
            widget = app.keyboardGrabber()
            if widget:
                widget.releaseKeyboard()
            
            # Process events to clear any pending operations
            app.processEvents()
        except:
            pass


def cleanup_qt_widget(widget):
    """Properly clean up a Qt widget, closing any windows and releasing grabs."""
    if widget is None:
        return
    
    # Release any mouse or keyboard grabs
    if hasattr(widget, 'releaseMouse'):
        try:
            widget.releaseMouse()
        except:
            pass
    
    if hasattr(widget, 'releaseKeyboard'):
        try:
            widget.releaseKeyboard()
        except:
            pass
    
    # Close the widget if it's a window
    if hasattr(widget, 'close'):
        try:
            widget.close()
        except:
            pass
    
    # Mark for deletion
    if hasattr(widget, 'deleteLater'):
        try:
            widget.deleteLater()
        except:
            pass
    
    # Process pending events to ensure deletion happens and grabs are released
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance()
    if app:
        try:
            app.processEvents()
        except:
            pass
