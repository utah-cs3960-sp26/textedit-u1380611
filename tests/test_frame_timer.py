"""Tests for the FrameTimer widget."""

import time
import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QWidget

from editor.frame_timer import FrameTimer


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def frame_timer(qapp):
    ft = FrameTimer()
    yield ft
    ft._stop_timing()
    ft.deleteLater()
    qapp.processEvents()


class TestFrameTimerInit:
    """Test initial state of the FrameTimer."""

    def test_hidden_by_default(self, frame_timer):
        assert not frame_timer.isVisible()

    def test_not_timing_by_default(self, frame_timer):
        assert not frame_timer._timing

    def test_empty_frame_times(self, frame_timer):
        assert frame_timer._frame_times == []

    def test_label_shows_placeholder(self, frame_timer):
        assert "--" in frame_timer._label.text()


class TestToggle:
    """Test toggle show/hide behavior."""

    def test_toggle_shows_widget(self, frame_timer):
        frame_timer.toggle()
        assert frame_timer.isVisible()
        assert frame_timer._timing

    def test_toggle_twice_hides_widget(self, frame_timer):
        frame_timer.toggle()
        frame_timer.toggle()
        assert not frame_timer.isVisible()
        assert not frame_timer._timing

    def test_toggle_hide_resets_stats(self, frame_timer):
        frame_timer.toggle()  # show
        frame_timer._record_frame(5.0)
        frame_timer._record_frame(10.0)
        assert len(frame_timer._frame_times) == 2

        frame_timer.toggle()  # hide → reset
        assert frame_timer._frame_times == []
        assert frame_timer._last_frame_ms == 0.0
        assert frame_timer._max_frame_ms == 0.0
        assert "--" in frame_timer._label.text()

    def test_refresh_timer_runs_while_visible(self, frame_timer):
        frame_timer.toggle()
        assert frame_timer._refresh_timer.isActive()

        frame_timer.toggle()
        assert not frame_timer._refresh_timer.isActive()

    def test_tick_timer_runs_while_visible(self, frame_timer):
        frame_timer.toggle()
        assert frame_timer._tick_timer.isActive()

        frame_timer.toggle()
        assert not frame_timer._tick_timer.isActive()


class TestRecordFrame:
    """Test frame recording logic."""

    def test_record_updates_last(self, frame_timer):
        frame_timer._record_frame(3.5)
        assert frame_timer._last_frame_ms == 3.5

    def test_record_tracks_max(self, frame_timer):
        frame_timer._record_frame(2.0)
        frame_timer._record_frame(8.0)
        frame_timer._record_frame(4.0)
        assert frame_timer._max_frame_ms == 8.0

    def test_average_calculation(self, frame_timer):
        frame_timer._record_frame(2.0)
        frame_timer._record_frame(4.0)
        frame_timer._record_frame(6.0)
        assert frame_timer._average_ms() == pytest.approx(4.0)

    def test_average_empty(self, frame_timer):
        assert frame_timer._average_ms() == 0.0

    def test_bounded_history(self, frame_timer):
        for i in range(600):
            frame_timer._record_frame(float(i))
        assert len(frame_timer._frame_times) == 500


class TestUpdateDisplay:
    """Test display label updates."""

    def test_display_no_data(self, frame_timer):
        frame_timer._update_display()
        assert "--" in frame_timer._label.text()

    def test_display_with_data(self, frame_timer):
        frame_timer._record_frame(5.0)
        frame_timer._update_display()
        text = frame_timer._label.text()
        assert "5.0" in text
        assert "Avg" in text
        assert "Max" in text


class TestEventFilter:
    """Test the event filter that captures input events."""

    def test_input_event_sets_recent_input(self, frame_timer, qapp):
        frame_timer.toggle()
        dummy = QWidget()

        assert not frame_timer._has_recent_input

        key_event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_A, Qt.KeyboardModifier.NoModifier)
        frame_timer.eventFilter(dummy, key_event)

        assert frame_timer._has_recent_input
        dummy.deleteLater()

    def test_event_filter_returns_false(self, frame_timer, qapp):
        frame_timer.toggle()
        dummy = QWidget()
        key_event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_A, Qt.KeyboardModifier.NoModifier)
        result = frame_timer.eventFilter(dummy, key_event)
        assert result is False
        dummy.deleteLater()

    def test_non_input_event_does_not_set_flag(self, frame_timer, qapp):
        frame_timer.toggle()
        dummy = QWidget()

        timer_event = QEvent(QEvent.Type.Timer)
        frame_timer.eventFilter(dummy, timer_event)

        assert not frame_timer._has_recent_input
        dummy.deleteLater()

    def test_input_starts_idle_timer(self, frame_timer, qapp):
        frame_timer.toggle()
        dummy = QWidget()

        key_event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_A, Qt.KeyboardModifier.NoModifier)
        frame_timer.eventFilter(dummy, key_event)

        assert frame_timer._idle_timer.isActive()
        dummy.deleteLater()


class TestTickMeasurement:
    """Test the 0ms timer tick that measures event-loop stalls."""

    def test_tick_records_when_input_active(self, frame_timer, qapp):
        """A tick after a previous tick with recent input should record."""
        frame_timer.toggle()
        frame_timer._has_recent_input = True
        frame_timer._last_tick = time.perf_counter() - 0.010  # 10ms ago

        frame_timer._on_tick()

        assert len(frame_timer._frame_times) == 1
        assert frame_timer._last_frame_ms >= 9.0  # ~10ms with tolerance

    def test_tick_does_not_record_without_input(self, frame_timer, qapp):
        """Ticks without recent input should not record frames."""
        frame_timer.toggle()
        frame_timer._has_recent_input = False
        frame_timer._last_tick = time.perf_counter() - 0.050

        frame_timer._on_tick()

        assert len(frame_timer._frame_times) == 0

    def test_tick_ignores_sub_1ms(self, frame_timer, qapp):
        """Sub-1ms ticks are idle event-loop iterations, not frames."""
        frame_timer.toggle()
        frame_timer._has_recent_input = True
        frame_timer._last_tick = time.perf_counter()  # just now

        frame_timer._on_tick()

        assert len(frame_timer._frame_times) == 0

    def test_tick_updates_last_tick(self, frame_timer, qapp):
        """Each tick should update _last_tick."""
        frame_timer.toggle()
        old = frame_timer._last_tick

        time.sleep(0.002)
        frame_timer._on_tick()

        assert frame_timer._last_tick > old

    def test_simulated_stall(self, frame_timer, qapp):
        """Simulate a 200ms main-thread stall and verify it's recorded."""
        frame_timer.toggle()
        frame_timer._has_recent_input = True
        frame_timer._last_tick = time.perf_counter() - 0.200  # 200ms ago

        frame_timer._on_tick()

        assert len(frame_timer._frame_times) == 1
        assert frame_timer._last_frame_ms >= 190.0


class TestTimingControl:
    """Test start/stop timing."""

    def test_start_twice_no_error(self, frame_timer, qapp):
        frame_timer._start_timing()
        frame_timer._start_timing()
        assert frame_timer._timing
        frame_timer._stop_timing()

    def test_stop_without_start_no_error(self, frame_timer, qapp):
        frame_timer._stop_timing()
        assert not frame_timer._timing

    def test_stop_removes_event_filter(self, frame_timer, qapp):
        frame_timer._start_timing()
        frame_timer._stop_timing()
        assert not frame_timer._timing

    def test_stop_timing_stops_idle_timer(self, frame_timer, qapp):
        frame_timer._start_timing()
        frame_timer._idle_timer.start()
        assert frame_timer._idle_timer.isActive()
        frame_timer._stop_timing()
        assert not frame_timer._idle_timer.isActive()


class TestIdleDetection:
    """Test flag-based idle detection."""

    def test_idle_timeout_clears_flag(self, frame_timer, qapp):
        frame_timer._has_recent_input = True
        frame_timer._on_idle_timeout()
        assert not frame_timer._has_recent_input

    def test_start_timing_initializes_flag_false(self, frame_timer, qapp):
        frame_timer._has_recent_input = True
        frame_timer._start_timing()
        assert not frame_timer._has_recent_input
        frame_timer._stop_timing()

    def test_reset_clears_flag(self, frame_timer):
        frame_timer._has_recent_input = True
        frame_timer._reset()
        assert not frame_timer._has_recent_input

    def test_idle_timeout_ms_value(self, frame_timer):
        assert frame_timer._IDLE_TIMEOUT_MS == 2000
        assert frame_timer._idle_timer.interval() == 2000

    def test_idle_timer_is_singleshot(self, frame_timer):
        assert frame_timer._idle_timer.isSingleShot()


class TestDisplayFormat:
    """Test the N: count in the display."""

    def test_display_shows_frame_count(self, frame_timer):
        frame_timer._record_frame(5.0)
        frame_timer._record_frame(10.0)
        frame_timer._update_display()
        text = frame_timer._label.text()
        assert "N: 2" in text

    def test_display_empty_shows_zero_count(self, frame_timer):
        frame_timer._update_display()
        assert "N: 0" in frame_timer._label.text()

    def test_display_shows_five_frames(self, frame_timer):
        for i in range(5):
            frame_timer._record_frame(float(i + 1))
        frame_timer._update_display()
        assert "N: 5" in frame_timer._label.text()
