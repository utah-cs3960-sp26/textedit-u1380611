"""
Virtual Document Module

Provides viewport-based document virtualization for large files.
Only a small window of lines (e.g. 5000) is loaded into the QTextDocument
at any time, giving O(1) open/scroll performance regardless of file size.
"""

import array
import bisect

from PySide6.QtCore import QObject, Qt, QTimer, Signal
from PySide6.QtGui import QTextCursor, QTextDocument, QWheelEvent
from PySide6.QtWidgets import QPlainTextDocumentLayout, QScrollBar


class LineIndex:
    """Fast line-start offset index for a raw content string.

    Uses a compact ``array.array('Q')`` so 1.47M entries ≈ 12 MB,
    compared to ~45 MB for a Python ``list[int]``.
    """

    __slots__ = ("_offsets", "_length")

    def __init__(self, content: str):
        offsets = array.array("Q")
        offsets.append(0)
        idx = 0
        while True:
            idx = content.find("\n", idx)
            if idx == -1:
                break
            offsets.append(idx + 1)
            idx += 1
        self._offsets = offsets
        self._length = len(offsets)

    @property
    def line_count(self) -> int:
        return self._length

    def line_start(self, line0: int) -> int:
        return self._offsets[line0]

    def line_end(self, line0: int, content_len: int) -> int:
        if line0 + 1 < self._length:
            return self._offsets[line0 + 1]
        return content_len

    def offset_to_line(self, offset: int) -> int:
        return bisect.bisect_right(self._offsets, offset) - 1

    def slice_lines(self, content: str, start_line0: int, count: int) -> str:
        """Return the text for ``count`` lines starting at ``start_line0``."""
        end_line0 = min(start_line0 + count, self._length) - 1
        start_off = self._offsets[start_line0]
        if end_line0 + 1 < self._length:
            end_off = self._offsets[end_line0 + 1]
        else:
            end_off = len(content)
        text = content[start_off:end_off]
        # Strip trailing newline so QTextDocument doesn't create an extra empty block
        if text.endswith("\n"):
            text = text[:-1]
        return text


class VirtualDocumentController(QObject):
    """Controls viewport-windowed loading of a large file into a QPlainTextEdit.

    The editor's QTextDocument only ever contains ``WINDOW`` lines.  A separate
    *global* scrollbar (owned by the caller) represents the full file.
    """

    WINDOW = 2000          # lines loaded into QTextDocument at a time
    MARGIN = 500           # swap hysteresis margin (lines)
    SCROLL_LINES = 3       # lines per wheel tick

    cursor_global_changed = Signal(int, int)  # global line (1-based), col (1-based)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._editor = None
        self._global_sb = None
        self._content: str = ""
        self._index: LineIndex | None = None
        self._window_start: int = 0      # first global line0 in the window
        self._window_lines: int = 0      # actual lines currently loaded
        self._active = False
        self._swapping = False           # guard against re-entrant swaps

        self._swap_timer = QTimer(self)
        self._swap_timer.setSingleShot(True)
        self._swap_timer.setInterval(16)   # coalesce to once per frame
        self._swap_timer.timeout.connect(self._do_swap)
        self._pending_global_top: int | None = None

    # ── attach / detach ──────────────────────────────────────────────

    def attach(self, editor, global_scrollbar: QScrollBar, content: str, index: LineIndex):
        """Set up virtualisation for *editor* backed by *content*."""
        self._editor = editor
        self._global_sb = global_scrollbar
        self._content = content
        self._index = index
        self._active = True

        # Hide internal scrollbar; use our global one
        editor.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        total = index.line_count
        visible = self._visible_lines()
        global_scrollbar.setMinimum(0)
        global_scrollbar.setMaximum(max(0, total - visible))
        global_scrollbar.setPageStep(visible)
        global_scrollbar.setSingleStep(self.SCROLL_LINES)
        global_scrollbar.setValue(0)
        global_scrollbar.valueChanged.connect(self._on_global_scroll)
        global_scrollbar.show()

        # Load initial window
        self._load_window(0)

        # Line-number gutter context
        editor.set_line_number_context(0, total)

        # Forward cursor changes
        editor.cursorPositionChanged.connect(self._on_cursor_moved)

    def detach(self):
        """Disconnect virtualisation."""
        if not self._active:
            return
        self._active = False
        self._swap_timer.stop()
        if self._global_sb is not None:
            try:
                self._global_sb.valueChanged.disconnect(self._on_global_scroll)
            except RuntimeError:
                pass
            self._global_sb.hide()
        if self._editor is not None:
            self._editor.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            try:
                self._editor.cursorPositionChanged.disconnect(self._on_cursor_moved)
            except RuntimeError:
                pass
            self._editor.set_line_number_context(0, None)
        self._editor = None
        self._global_sb = None
        self._index = None

    @property
    def active(self) -> bool:
        return self._active

    @property
    def window_start(self) -> int:
        return self._window_start

    # ── public API ───────────────────────────────────────────────────

    def visible_lines(self) -> int:
        return self._visible_lines()

    def ensure_global_line_visible(self, line0: int, center: bool = False):
        """Scroll so that *line0* is visible, loading a new window if needed."""
        if not self._active:
            return
        visible = self._visible_lines()
        if center:
            target_top = max(0, line0 - visible // 2)
        else:
            current_top = self._global_sb.value()
            if current_top <= line0 <= current_top + visible - 1:
                return  # already visible
            if line0 < current_top:
                target_top = line0
            else:
                target_top = line0 - visible + 1
        target_top = max(0, min(target_top, self._global_sb.maximum()))
        self._global_sb.setValue(target_top)

    def set_cursor_global(self, line0: int, col0: int):
        """Move the editor cursor to a global position."""
        if not self._active:
            return
        # Ensure the target line is in the loaded window (immediate, not deferred)
        self._ensure_window_contains(line0)
        self.ensure_global_line_visible(line0, center=True)
        self._set_local_cursor(line0, col0)

    def goto_global_offset(self, offset: int):
        """Jump cursor to a global character offset (e.g. from find)."""
        if not self._active or self._index is None:
            return
        line0 = self._index.offset_to_line(offset)
        col0 = offset - self._index.line_start(line0)
        self.set_cursor_global(line0, col0)

    def save_state(self):
        """Return virtualisation state for tab-switch persistence."""
        return {
            "window_start": self._window_start,
            "global_top": self._global_sb.value() if self._global_sb else 0,
        }

    def restore_state(self, state: dict):
        """Restore previously saved virtualisation state."""
        ws = state.get("window_start", 0)
        gt = state.get("global_top", 0)
        self._load_window(ws)
        if self._global_sb:
            self._global_sb.setValue(gt)

    def handle_wheel(self, event: QWheelEvent):
        """Route wheel events to the global scrollbar."""
        if not self._active or self._global_sb is None:
            return
        delta = event.angleDelta().y()
        steps = -(delta // 120) * self.SCROLL_LINES
        self._global_sb.setValue(self._global_sb.value() + steps)

    # ── internal ─────────────────────────────────────────────────────

    def _visible_lines(self) -> int:
        if self._editor is None:
            return 40
        fm = self._editor.fontMetrics()
        lh = fm.lineSpacing()
        if lh <= 0:
            lh = 16
        vh = self._editor.viewport().height()
        return max(1, vh // lh)

    def _ensure_window_contains(self, line0: int):
        """Immediately load a window containing *line0* if not already loaded."""
        if self._window_start <= line0 < self._window_start + self._window_lines:
            return  # already in window
        total = self._index.line_count if self._index else 0
        new_start = max(0, line0 - self.WINDOW // 2)
        if new_start + self.WINDOW > total:
            new_start = max(0, total - self.WINDOW)
        self._load_window(new_start)

    def _on_global_scroll(self, value: int):
        """Global scrollbar moved – translate to local scroll or request swap.

        Uses hysteresis (MARGIN) so small movements within the loaded window
        are handled by the local scrollbar without a window swap.
        """
        if self._swapping:
            return
        local_line = value - self._window_start
        usable = self._window_lines - self._visible_lines()
        if 0 <= local_line <= usable:
            self._scroll_local(local_line)
            return

        # Need window swap — coalesce via timer
        self._pending_global_top = value
        if not self._swap_timer.isActive():
            self._swap_timer.start()

    def _scroll_local(self, local_line: int):
        """Scroll the editor's internal scrollbar to *local_line*."""
        if self._editor is None:
            return
        sb = self._editor.verticalScrollBar()
        sb.setValue(local_line)

    def _do_swap(self):
        """Execute a deferred window swap."""
        if not self._active or self._pending_global_top is None:
            return
        target = self._pending_global_top
        self._pending_global_top = None

        # Centre the window around the target line
        new_start = max(0, target - self.WINDOW // 2)
        total = self._index.line_count if self._index else 0
        if new_start + self.WINDOW > total:
            new_start = max(0, total - self.WINDOW)
        self._load_window(new_start)
        local_line = target - self._window_start
        self._scroll_local(max(0, local_line))

    def _load_window(self, start_line0: int):
        """Load ``WINDOW`` lines starting at *start_line0* into the editor."""
        if self._editor is None or self._index is None:
            return
        self._swapping = True
        total = self._index.line_count
        start_line0 = max(0, min(start_line0, max(0, total - 1)))
        count = min(self.WINDOW, total - start_line0)

        text = self._index.slice_lines(self._content, start_line0, count)

        doc = self._editor.document()
        doc.blockSignals(True)
        self._editor.blockSignals(True)
        self._editor.setUpdatesEnabled(False)

        doc.setUndoRedoEnabled(False)
        doc.setPlainText(text)
        doc.setUndoRedoEnabled(True)

        self._editor.setUpdatesEnabled(True)
        self._editor.blockSignals(False)
        doc.blockSignals(False)

        self._window_start = start_line0
        self._window_lines = count

        # Update gutter
        self._editor.set_line_number_context(start_line0, total)
        self._swapping = False

    def _set_local_cursor(self, global_line0: int, col0: int):
        """Set the editor cursor to a global position (must be in current window)."""
        if self._editor is None:
            return
        local_line = global_line0 - self._window_start
        if local_line < 0 or local_line >= self._window_lines:
            return  # not in window
        block = self._editor.document().findBlockByLineNumber(local_line)
        if not block.isValid():
            return
        pos = block.position() + min(col0, max(0, block.length() - 1))
        cursor = self._editor.textCursor()
        cursor.setPosition(pos)
        self._editor.setTextCursor(cursor)

    def _on_cursor_moved(self):
        """Translate local cursor to global and emit."""
        if self._swapping or self._editor is None:
            return
        cursor = self._editor.textCursor()
        local_line = cursor.blockNumber()
        col = cursor.columnNumber()
        global_line = self._window_start + local_line
        self.cursor_global_changed.emit(global_line + 1, col + 1)
