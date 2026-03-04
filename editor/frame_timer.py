"""
Frame Timer Widget

Measures how long the GUI thread is blocked (dropped frames).
A "frame" is the wall-clock time between consecutive returns to the
event loop.  If the main thread is blocked for 50ms doing layout work,
that shows up as a 50ms frame.

Activated via Ctrl+P.  Resets and stops timing when hidden.
"""

import time

from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout
from PySide6.QtCore import QTimer, Qt, QEvent


class FrameTimer(QWidget):
    """Overlay widget showing frame timing statistics.

    Uses a 0ms repeating timer to detect event-loop stalls.
    A QTimer with 0ms interval fires once per event-loop iteration.
    If two consecutive firings are separated by >1ms it means the
    main thread was busy for that long — a dropped frame.
    """

    _IDLE_TIMEOUT_MS = 2000   # no input for this long → stop recording
    _MIN_FRAME_MS = 1.0       # ignore sub-1ms idle ticks

    def __init__(self, parent=None):
        super().__init__(parent)

        self._timing = False
        self._frame_times: list[float] = []
        self._last_frame_ms: float = 0.0
        self._max_frame_ms: float = 0.0

        self._last_tick: float = 0.0
        self._has_recent_input: bool = False

        self._setup_ui()

        # 0ms timer fires once per event-loop iteration
        self._tick_timer = QTimer(self)
        self._tick_timer.setInterval(0)
        self._tick_timer.timeout.connect(self._on_tick)

        # Display refresh (10 Hz)
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setInterval(100)
        self._refresh_timer.timeout.connect(self._update_display)

        # Idle detection — stop recording when the user stops interacting
        self._idle_timer = QTimer(self)
        self._idle_timer.setSingleShot(True)
        self._idle_timer.setInterval(self._IDLE_TIMEOUT_MS)
        self._idle_timer.timeout.connect(self._on_idle_timeout)

        self.hide()

    # ── UI ───────────────────────────────────────────────────────────

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 2, 6, 2)

        self._label = QLabel("Frame: --  Avg: --  Max: --  N: 0")
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
        self._last_tick = time.perf_counter()
        self._has_recent_input = False
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance()
        if app:
            app.installEventFilter(self)
        self._tick_timer.start()
        self._refresh_timer.start()

    def _stop_timing(self):
        if not self._timing:
            return
        self._timing = False
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance()
        if app:
            app.removeEventFilter(self)
        self._tick_timer.stop()
        self._refresh_timer.stop()
        self._idle_timer.stop()

    def _reset(self):
        self._frame_times.clear()
        self._last_frame_ms = 0.0
        self._max_frame_ms = 0.0
        self._last_tick = 0.0
        self._has_recent_input = False
        self._label.setText("Frame: --  Avg: --  Max: --  N: 0")

    # ── Idle detection ───────────────────────────────────────────────

    def _on_idle_timeout(self):
        self._has_recent_input = False

    # ── Event filter (only for input detection) ──────────────────────

    _INPUT_EVENTS = frozenset({
        QEvent.Type.KeyPress,
        QEvent.Type.MouseButtonPress,
        QEvent.Type.MouseButtonRelease,
        QEvent.Type.Wheel,
        QEvent.Type.InputMethod,
    })

    def eventFilter(self, obj, event):  # noqa: N802
        if event.type() in self._INPUT_EVENTS:
            self._has_recent_input = True
            self._idle_timer.start()
        return False

    # ── Tick — fires once per event-loop iteration ───────────────────

    def _on_tick(self):
        now = time.perf_counter()
        if self._last_tick > 0 and self._has_recent_input:
            elapsed_ms = (now - self._last_tick) * 1000.0
            if elapsed_ms >= self._MIN_FRAME_MS:
                self._record_frame(elapsed_ms)
        self._last_tick = now

    # ── Recording & display ──────────────────────────────────────────

    def _record_frame(self, ms: float):
        self._last_frame_ms = ms
        if ms > self._max_frame_ms:
            self._max_frame_ms = ms
        self._frame_times.append(ms)
        if len(self._frame_times) > 500:
            self._frame_times = self._frame_times[-500:]

    def _average_ms(self) -> float:
        if not self._frame_times:
            return 0.0
        return sum(self._frame_times) / len(self._frame_times)

    def _update_display(self):
        if not self._frame_times:
            self._label.setText("Frame: --  Avg: --  Max: --  N: 0")
            return
        self._label.setText(
            f"Frame: {self._last_frame_ms:6.1f}ms  "
            f"Avg: {self._average_ms():6.1f}ms  "
            f"Max: {self._max_frame_ms:6.1f}ms  "
            f"N: {len(self._frame_times)}"
        )
