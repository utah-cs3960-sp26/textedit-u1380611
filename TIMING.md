Initial Timings-

Small.txt-
    Max open time: 38
    Max scroll time:29
    Max click far:72
    Avg click far: 45
    Max replace time: 150
    Total Memory:196Mb

Medium.txt-
    Max open time: 121
    Max scroll time: 80
    Max click far: 94
    Avg click far: 55
    Max replace time: 253
    Total Memory: 223Mb

Large.txt-
    Max open time: 1246
    Max scroll time: 75
    Max click far: 96
    Avg click far: 75
    Max replace time: DNE, tried 10+ times, can't get past find search step, app completely freezes and crashes
    Total Memory: 2.2Gb

After optimizing:

Small.txt-
    Max open time: 36
    Max scroll time: 6
    Max click far: 45
    Avg click far: 10
    Max replace time: 27
    Total Memory: 194Mb

Medium.txt-
    Max open time: 116
    Max scroll time: 47
    Max click far: 89
    Avg click far: 60
    Max replace time: 40
    Total Memory: 202 Mb

Large.txt-
    Max open time: 645
    Max scroll time: 50
    Max click far: 77
    Avg click far: 55
    Max replace time: 2639
    Total Memory: 1.8Gb


Optimizations Added (Week 8)-

Find & Replace:
- Debounced search: 300ms delay so typing "while" triggers one search, not five
- Viewport-only highlighting: only highlights matches visible on screen, uses bisect for fast lookup
- Lightweight storage: stores (start, end) tuples and a precomputed starts list for binary search
- Bulk Replace All: uses str.replace/re.subn for >1000 matches instead of individual cursor edits
- Cached search content: reuses the original file string for searching instead of calling toPlainText() each time
File I/O:
- mmap for large files: files >1MB are read via memory-mapped I/O, reducing buffer copies
Memory:
- Skipped toHtml() for plain text: avoids generating HTML 3-5x larger than the raw text on tab switch
- Dirty tracking: only calls toPlainText() on tab switch when text was actually edited
- Auto-disable word wrap: turns off line-wrap layout for files >1MB to avoid expensive per-block computation

Further Optimizations Added (Week 8+)-

Libraries used: none beyond PySide6 (Qt6). All optimizations use Qt's own APIs.

Tab Switching / Click Far:
- QTextDocument caching: on tab switch, the live QTextDocument is saved on the Document
  model and swapped back in via QPlainTextEdit.setDocument() instead of rebuilding it
  from scratch with setPlainText(). This avoids reconstructing ~1.47M QTextBlock objects
  for large files on every tab switch. New documents get a fresh QTextDocument with
  QPlainTextDocumentLayout so the old one stays intact.

Scroll Performance:
- Removed redundant gutter width recalculation: the line number area width was being
  recalculated on every scroll via setViewportMargins(), which triggers relayout cascades.
  Width now only updates on blockCountChanged and resize, not on scroll.
- Coalesced scroll highlight refresh: FindReplaceDialog now uses a 0ms single-shot QTimer
  to batch multiple updateRequest signals into one highlight refresh per frame, instead of
  calling _update_highlights() for every scroll event.

File Loading:
- Chunked insertion for large files (>1MB): instead of one massive setPlainText() call that
  freezes the UI for 645ms+, content is inserted in 2MB chunks via QTextCursor.insertText()
  with QCoreApplication.processEvents() between chunks. Updates and undo are disabled during
  loading to minimize per-chunk overhead.

Replace All:
- Disabled updates and undo during bulk replace: for >1000 matches, setUpdatesEnabled(False)
  and setUndoRedoEnabled(False) are set before setPlainText(new_content) and restored after,
  reducing the GUI stall from the document rebuild.

Week 9 Optimizations-

Libraries used: none beyond PySide6 (Qt6) and Python stdlib (array, bisect, concurrent.futures).

- Virtualised document loading for large files (>5MB): only 5000 lines are loaded into
  QTextDocument at any time instead of all 1.47M lines. A LineIndex (compact array.array('Q'))
  maps every line-start offset (~12MB for 1.47M lines). The index is built in a background
  thread (ThreadPoolExecutor) so the GUI shows a "Loading…" placeholder instantly with zero
  stall. Once ready, the first 5000-line window loads in <1ms.

- Global scrollbar for virtualised files: a separate QScrollBar represents the full file
  (range = total lines). The editor's built-in scrollbar is hidden. Small scroll movements
  adjust the local scrollbar within the loaded window. When scrolling near a window edge,
  a new 5000-line window is swapped in (<5ms) with hysteresis (1200-line margin) to avoid
  thrashing. Swaps are coalesced via QTimer.singleShot(0).

- Fast cursor navigation for virtualised files: set_cursor_global() immediately loads a
  window centred on the target line, so jumps (including find-next) complete in <5ms
  regardless of position. QTextDocument only has 5000 blocks so Qt layout is trivial.

- Global line number offset in gutter: LineNumberedEditor.set_line_number_context() accepts
  a base_line0 offset so the gutter displays (base + block_number + 1) for correct global
  line numbers. line_number_area_width() uses the full file's line count for digit width.

- Wheel event routing: LineNumberedEditor.wheelEvent() routes through the virtual controller
  when active, scrolling the global scrollbar instead of the hidden local one.

- Virtual state persistence on tab switch: window_start and global_top are saved on the
  Document model. On restore, the cached LineIndex is reused (no rebuild) and the previous
  window/scroll position is restored. Document.content is never overwritten from the editor
  (which only holds the viewport window).

- Fixed frame timer measurement: rewrote FrameTimer to use a 0ms QTimer tick that fires once
  per event-loop iteration. Time between consecutive ticks = time the main thread was blocked.
  Old timer had several bugs: measured input-to-paint latency instead of actual stall time,
  double-counted stalls via both paint and gap detection paths, MouseMove flooding caused
  artificially low/noisy readings, and file-open stalls were missed when no user input was
  active.

- Removed MouseMove from frame timer input events: only KeyPress, MouseButtonPress/Release,
  Wheel, and InputMethod are tracked. MouseMove floods during scrolling were resetting the
  input timestamp every few ms, making stall measurements unreliable.

- Fixed accumulating cursorPositionChanged signal connections: MainWindow._on_document_changed
  now disconnects before reconnecting, preventing the handler from firing multiple times per
  cursor move after switching documents.

- Global line numbers in status bar: _on_cursor_position_changed and _update_status_bar now
  use editor._line_number_base to display correct global line numbers for virtualised docs.