"""
Tests for the virtual document module (LineIndex and VirtualDocumentController).
"""

import pytest
from PySide6.QtWidgets import QApplication, QScrollBar
from PySide6.QtCore import Qt

from editor.virtual_document import LineIndex, VirtualDocumentController
from editor.line_number_editor import LineNumberedEditor
from tests.conftest import cleanup_qt_widget


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


# ── LineIndex tests ──────────────────────────────────────────────────


class TestLineIndex:
    def test_empty_content(self):
        idx = LineIndex("")
        assert idx.line_count == 1
        assert idx.line_start(0) == 0

    def test_single_line_no_newline(self):
        idx = LineIndex("hello")
        assert idx.line_count == 1
        assert idx.line_start(0) == 0
        assert idx.line_end(0, 5) == 5

    def test_single_line_with_newline(self):
        idx = LineIndex("hello\n")
        assert idx.line_count == 2
        assert idx.line_start(0) == 0
        assert idx.line_start(1) == 6

    def test_multiple_lines(self):
        content = "line0\nline1\nline2\n"
        idx = LineIndex(content)
        assert idx.line_count == 4  # 3 lines + empty line after trailing \n
        assert idx.line_start(0) == 0
        assert idx.line_start(1) == 6
        assert idx.line_start(2) == 12

    def test_offset_to_line(self):
        content = "aaa\nbbb\nccc\n"
        idx = LineIndex(content)
        assert idx.offset_to_line(0) == 0
        assert idx.offset_to_line(1) == 0
        assert idx.offset_to_line(3) == 0   # the \n itself
        assert idx.offset_to_line(4) == 1   # start of line1
        assert idx.offset_to_line(7) == 1
        assert idx.offset_to_line(8) == 2

    def test_slice_lines(self):
        content = "line0\nline1\nline2\nline3\n"
        idx = LineIndex(content)
        # Slice lines 1..2 (0-based)
        text = idx.slice_lines(content, 1, 2)
        assert text == "line1\nline2"

    def test_slice_lines_from_start(self):
        content = "aaa\nbbb\nccc\n"
        idx = LineIndex(content)
        text = idx.slice_lines(content, 0, 2)
        assert text == "aaa\nbbb"

    def test_slice_lines_to_end(self):
        content = "aaa\nbbb\nccc"
        idx = LineIndex(content)
        text = idx.slice_lines(content, 1, 100)
        assert text == "bbb\nccc"

    def test_large_content(self):
        lines = [f"line {i}\n" for i in range(10000)]
        content = "".join(lines)
        idx = LineIndex(content)
        assert idx.line_count == 10001  # 10000 lines + empty after trailing \n
        # Check a line in the middle
        assert idx.offset_to_line(idx.line_start(5000)) == 5000
        text = idx.slice_lines(content, 5000, 3)
        assert text == "line 5000\nline 5001\nline 5002"


# ── VirtualDocumentController tests ──────────────────────────────────


class TestVirtualDocumentController:
    @pytest.fixture
    def editor(self, qapp):
        e = LineNumberedEditor()
        yield e
        cleanup_qt_widget(e)

    @pytest.fixture
    def scrollbar(self, qapp):
        sb = QScrollBar(Qt.Orientation.Vertical)
        yield sb
        cleanup_qt_widget(sb)

    @pytest.fixture
    def large_content(self):
        lines = [f"line number {i} with some content\n" for i in range(20000)]
        return "".join(lines)

    def test_attach_detach(self, editor, scrollbar, large_content):
        idx = LineIndex(large_content)
        ctrl = VirtualDocumentController()
        ctrl.attach(editor, scrollbar, large_content, idx)
        assert ctrl.active
        assert scrollbar.isVisible()
        assert scrollbar.maximum() > 0
        ctrl.detach()
        assert not ctrl.active

    def test_initial_load(self, editor, scrollbar, large_content):
        idx = LineIndex(large_content)
        ctrl = VirtualDocumentController()
        ctrl.attach(editor, scrollbar, large_content, idx)
        # Editor should have WINDOW lines loaded
        block_count = editor.document().blockCount()
        assert block_count <= VirtualDocumentController.WINDOW + 1
        assert block_count > 0
        ctrl.detach()

    def test_scrollbar_range(self, editor, scrollbar, large_content):
        idx = LineIndex(large_content)
        ctrl = VirtualDocumentController()
        ctrl.attach(editor, scrollbar, large_content, idx)
        assert scrollbar.minimum() == 0
        assert scrollbar.maximum() > 0
        assert scrollbar.maximum() <= idx.line_count
        ctrl.detach()

    def test_line_number_context(self, editor, scrollbar, large_content):
        idx = LineIndex(large_content)
        ctrl = VirtualDocumentController()
        ctrl.attach(editor, scrollbar, large_content, idx)
        # Gutter should show the correct total
        assert editor._line_number_total == idx.line_count
        assert editor._line_number_base == 0
        ctrl.detach()

    def test_set_cursor_global(self, editor, scrollbar, large_content):
        idx = LineIndex(large_content)
        ctrl = VirtualDocumentController()
        ctrl.attach(editor, scrollbar, large_content, idx)
        ctrl.set_cursor_global(100, 5)
        cursor = editor.textCursor()
        local_line = cursor.blockNumber()
        global_line = ctrl.window_start + local_line
        assert global_line == 100
        ctrl.detach()

    def test_save_restore_state(self, editor, scrollbar, large_content):
        idx = LineIndex(large_content)
        ctrl = VirtualDocumentController()
        ctrl.attach(editor, scrollbar, large_content, idx)
        scrollbar.setValue(500)
        state = ctrl.save_state()
        assert "window_start" in state
        assert "global_top" in state
        ctrl.detach()

        # Re-attach and restore
        ctrl2 = VirtualDocumentController()
        ctrl2.attach(editor, scrollbar, large_content, idx)
        ctrl2.restore_state(state)
        assert scrollbar.value() == state["global_top"]
        ctrl2.detach()

    def test_goto_global_offset(self, editor, scrollbar, large_content):
        idx = LineIndex(large_content)
        ctrl = VirtualDocumentController()
        ctrl.attach(editor, scrollbar, large_content, idx)
        # Jump to an offset in the middle
        mid_offset = len(large_content) // 2
        ctrl.goto_global_offset(mid_offset)
        expected_line = idx.offset_to_line(mid_offset)
        cursor = editor.textCursor()
        actual_global = ctrl.window_start + cursor.blockNumber()
        assert actual_global == expected_line
        ctrl.detach()

    def test_wheel_handler(self, editor, scrollbar, large_content):
        idx = LineIndex(large_content)
        ctrl = VirtualDocumentController()
        ctrl.attach(editor, scrollbar, large_content, idx)
        editor._virtual_wheel_handler = ctrl.handle_wheel
        assert editor._virtual_wheel_handler is not None
        ctrl.detach()
        editor._virtual_wheel_handler = None


# ── LineNumberedEditor virtualisation support ────────────────────────


class TestLineNumberedEditorVirtual:
    @pytest.fixture
    def editor(self, qapp):
        e = LineNumberedEditor()
        yield e
        cleanup_qt_widget(e)

    def test_set_line_number_context(self, editor):
        editor.set_line_number_context(100, 50000)
        assert editor._line_number_base == 100
        assert editor._line_number_total == 50000

    def test_reset_line_number_context(self, editor):
        editor.set_line_number_context(100, 50000)
        editor.set_line_number_context(0, None)
        assert editor._line_number_base == 0
        assert editor._line_number_total is None

    def test_line_number_area_width_with_total(self, editor):
        editor.setPlainText("hello\nworld")
        w_normal = editor.line_number_area_width()
        editor.set_line_number_context(0, 1000000)
        w_virtual = editor.line_number_area_width()
        # Virtual width should be wider (7-digit line numbers vs 1-digit)
        assert w_virtual > w_normal
