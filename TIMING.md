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

Timing After Week 9 Optimizations-
Small.txt-
    Max open time: 40
    Max scroll time: 5.3
    Max click far: 6.8
    Avg click far: 4.8
    Max replace time: 9.2
    Total Memory: 191

Medium.txt-
    Max open time: 74
    Max scroll time:7.8 
    Max click far: 8.8
    Avg click far: 4.2
    Max replace time: 12.6
    Total Memory: 201

Large.txt-
    Max open time: 603
    Max scroll time:13.9 
    Max click far: 29
    Avg click far: 10.3
    Max replace time: 182
    Total Memory: 508

Note: I also did some upgrades to my frame counter and it may have been wrong last week, so times here are probably more reflective of how the program is actually behaving. 

Optimizations Added (Week 9)-

Here is a quick summary of the major changes made this week-
Libraries used: PySide6 (Qt6) and Python stdlib (threading, array, bisect, concurrent.futures).
File Opening:
- Virtualised document loading for files >2MB: only 2000 lines are loaded into the
  QTextDocument at a time. A compact LineIndex (array.array) maps every line offset
  and is built in a background thread. The GUI shows content instantly with zero stall.
Scroll Performance:
- Unified extra-selection ownership: LineNumberedEditor merges current-line and
  search highlights into a single setExtraSelections() call, eliminating the
  constant overwrite fight that caused redundant repaints on every cursor move.
- Virtual scrollbar with 2000-line window swaps coalesced to once per frame (16ms).
Find & Replace:
- All searches run in a background thread with a cancellable generation counter
  that aborts stale searches every 5000 matches.
- Replace All (>1000 matches) runs the string replacement in a background thread,
  then rebuilds the document incrementally with the same 128KB/8ms budget loader.
- Viewport-only highlighting: only visible matches are highlighted (bisect lookup)
  when total matches exceed 500, avoiding expensive setExtraSelections with
  thousands of selections.
Memory:
- Skipped toHtml() for plain text files (avoids 3–5× memory bloat on tab switch).

When opening files, frames will always be dropped because QTextDocument.setPlainText() must parse and lay out the text from the document. Even with the newly added 2000 line window loadr, the initial chunks must be loaded and laid out on the page. This would be bad practice to do on a background thread because QT widgets aren't thread safe. In larger files, the find/replace all will always cause frame drops, AMP implemented a 128KB/8ms budget reloader on a thread, so the screen won't freeze when typing in the f/r, but the final repaint will always have to happen. Clicking far on large documents will also always cause a frame drop because we transitioned to a 2000 line at a time painting approach, so clicking far will have to draw a new 2000 lines at once. 
There are no slower operations than before, AMP did well at optimizing operations and trying to get them to 16ms. Multi line find and replace would be much harder now because we're breaking the document into 2000 line sections, so we would have to go through more of these sections rather than having one QTextDocument in the backend. Deleting a line for larger documents is now slower that we're using virtualization, as the content will have to be updated and the LineIndex will have to be updated for the offset rather than the old removeSelectedText() method. Multiple split views would also be slower now because each (larger) split view file will need it's own VirtualDocumentController but they'd all reference the same content string, so it would have to be sychronized and updated across all virtualizations where the old version would have just shared the same QTextDocument and share edits made to it. 