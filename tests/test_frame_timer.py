"""Tests for the FrameTimer widget."""

import time
import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QKeyEvent, QPaintEvent
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
    """Test the event filter that captures frame timings."""

    def test_input_event_sets_last_input_time(self, frame_timer, qapp):
        frame_timer.toggle()  # start timing
        dummy = QWidget()

        before = time.perf_counter()
        key_event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_A, Qt.KeyboardModifier.NoModifier)
        frame_timer.eventFilter(dummy, key_event)
        after = time.perf_counter()

        assert before <= frame_timer._last_input_time <= after
        dummy.deleteLater()

    def test_paint_after_input_records_frame(self, frame_timer, qapp):
        frame_timer.toggle()
        dummy = QWidget()

        # Simulate input
        key_event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_A, Qt.KeyboardModifier.NoModifier)
        frame_timer.eventFilter(dummy, key_event)

        # Small delay so the paint comes after input
        time.sleep(0.001)

        # Simulate paint
        paint_event = QPaintEvent(dummy.rect())
        frame_timer.eventFilter(dummy, paint_event)

        assert len(frame_timer._frame_times) == 1
        assert frame_timer._last_frame_ms > 0
        dummy.deleteLater()

    def test_paint_without_input_not_recorded(self, frame_timer, qapp):
        frame_timer.toggle()
        dummy = QWidget()

        # Set a past paint time but no input
        frame_timer._last_paint_time = time.perf_counter()
        frame_timer._last_input_time = 0.0

        paint_event = QPaintEvent(dummy.rect())
        frame_timer.eventFilter(dummy, paint_event)

        assert len(frame_timer._frame_times) == 0
        dummy.deleteLater()

    def test_event_filter_returns_false(self, frame_timer, qapp):
        frame_timer.toggle()
        dummy = QWidget()
        key_event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_A, Qt.KeyboardModifier.NoModifier)
        result = frame_timer.eventFilter(dummy, key_event)
        assert result is False
        dummy.deleteLater()


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
