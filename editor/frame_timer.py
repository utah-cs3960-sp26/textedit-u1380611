"""
Frame Timer Widget

Displays last, average, and max frame timings with idle time subtracted.
Activated via Ctrl+P. Resets and stops timing when hidden.
"""

import time

from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout
from PySide6.QtCore import QTimer, Qt, QEvent


class FrameTimer(QWidget):
    """Overlay widget showing frame timing statistics.

    Installs an application-level event filter to measure time spent
    processing non-idle frames (paint events that follow user input).
    """

    _IDLE_THRESHOLD_S = 0.10  # seconds without input → idle

    def __init__(self, parent=None):
        super().__init__(parent)

        self._timing = False
        self._frame_times: list[float] = []
        self._last_frame_ms: float = 0.0
        self._max_frame_ms: float = 0.0

        self._last_input_time: float = 0.0
        self._last_paint_time: float = 0.0
        self._last_event_time: float = 0.0

        self._setup_ui()

        self._refresh_timer = QTimer(self)
        self._refresh_timer.setInterval(100)
        self._refresh_timer.timeout.connect(self._update_display)

        self.hide()

    # ── UI ───────────────────────────────────────────────────────────

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 2, 6, 2)

        self._label = QLabel("Frame: --  Avg: --  Max: --")
        self._label.setStyleSheet(
            "QLabel { color: #00ff00; background: rgba(0,0,0,180);"
            " padding: 2px 6px; border-radius: 3px;"
            " font-family: monospace; font-size: 11px; }"
        )
        layout.addWidget(self._label)
        self.setFixedHeight(24)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    # ── Public API ───────────────────────────────────────────────────

    def toggle(self):
        """Toggle visibility, timing, and reset stats."""
        if self.isVisible():
            self._stop_timing()
            self._reset()
            self.hide()
        else:
            self.show()
            self._start_timing()

    # ── Timing control ───────────────────────────────────────────────

    def _start_timing(self):
        if self._timing:
            return
        self._timing = True
        self._last_paint_time = time.perf_counter()
        self._last_input_time = 0.0
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance()
        if app:
            app.installEventFilter(self)
        self._refresh_timer.start()

    def _stop_timing(self):
        if not self._timing:
            return
        self._timing = False
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance()
        if app:
            app.removeEventFilter(self)
        self._refresh_timer.stop()

    def _reset(self):
        self._frame_times.clear()
        self._last_frame_ms = 0.0
        self._max_frame_ms = 0.0
        self._last_input_time = 0.0
        self._last_paint_time = 0.0
        self._last_event_time = 0.0
        self._label.setText("Frame: --  Avg: --  Max: --")

    # ── Event filter ─────────────────────────────────────────────────

    _INPUT_EVENTS = frozenset({
        QEvent.Type.KeyPress,
        QEvent.Type.KeyRelease,
        QEvent.Type.MouseButtonPress,
        QEvent.Type.MouseButtonRelease,
        QEvent.Type.MouseMove,
        QEvent.Type.Wheel,
        QEvent.Type.InputMethod,
    })

    _STALL_THRESHOLD_MS = 200  # event-loop blocks longer than this are recorded

    def eventFilter(self, obj, event):  # noqa: N802
        now = time.perf_counter()
        etype = event.type()

        if etype in self._INPUT_EVENTS:
            self._last_input_time = now

        elif etype == QEvent.Type.Paint:
            if self._last_paint_time > 0 and self._last_input_time > 0:
                # Only record if there was input since the last paint
                if self._last_input_time > self._last_paint_time:
                    frame_ms = (now - self._last_input_time) * 1000.0
                    self._record_frame(frame_ms)
            self._last_paint_time = now

        # Stall detection: if there is a large gap between consecutive events
        # and there was recent user input, the main thread was blocked
        # (e.g. find/replace search freezing the UI).  The input→paint path
        # above can miss these when an intermediate widget paint resets the
        # tracker before the blocking work starts.
        if self._last_event_time > 0 and self._last_input_time > 0:
            gap_ms = (now - self._last_event_time) * 1000.0
            # How long before this gap started was the last input?
            input_age_s = self._last_event_time - self._last_input_time
            if gap_ms > self._STALL_THRESHOLD_MS and 0 <= input_age_s < 1.0:
                self._record_frame(gap_ms)

        self._last_event_time = now

        return False

    # ── Recording & display ──────────────────────────────────────────

    def _record_frame(self, ms: float):
        self._last_frame_ms = ms
        if ms > self._max_frame_ms:
            self._max_frame_ms = ms
        self._frame_times.append(ms)
        # Keep bounded so average stays meaningful over recent history
        if len(self._frame_times) > 500:
            self._frame_times = self._frame_times[-500:]

    def _average_ms(self) -> float:
        if not self._frame_times:
            return 0.0
        return sum(self._frame_times) / len(self._frame_times)

    def _update_display(self):
        if not self._frame_times:
            self._label.setText("Frame: --  Avg: --  Max: --")
            return
        self._label.setText(
            f"Frame: {self._last_frame_ms:6.1f}ms  "
            f"Avg: {self._average_ms():6.1f}ms  "
            f"Max: {self._max_frame_ms:6.1f}ms"
        )
