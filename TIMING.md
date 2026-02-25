Initial Timings-

Small.txt-
    Max open time: 38
    Max scroll time:29
    Max click far:72
    Avg click far: 45
    Max replace time: 150
    Total Memory:196Mb

Medium.txt-
    Max open time: 101
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
    Max replace time: DNE, tried 10+ times, can't get past find step, app completely freezes
    Total Memory: 2.2Gb

Optimizations Applied-

Find & Replace:
- Viewport-only highlighting: only creates ExtraSelections for visible matches (bisect lookup), refreshes on scroll
- Debounced search (300ms): typing "while" triggers ONE search instead of 5 (one per keystroke)
- Lightweight match storage: stores (start, end) tuples instead of full SearchMatch objects for single-file dialog
- Cached match_starts list: precomputed once per search instead of rebuilt on every scroll/highlight
- String-based Replace All: uses str.replace/re.subn for >1000 matches instead of N individual cursor operations
- Bisect for current match lookup: uses binary search instead of linear scan to find nearest match to cursor
- regex case-insensitive search: uses re.finditer with re.IGNORECASE instead of content.lower() (avoids 253MB string copy)
- Eliminated content.split('\n'): scans for newline positions instead of creating 1.47M string objects

Memory:
- Removed toHtml() for plain text: skips HTML generation in _save_current_state (HTML was 3-5x larger than plain text)
- Content dirty tracking: only calls toPlainText() on tab switch when text was actually edited
- Auto-disable word wrap for large files: prevents Qt from computing line-wrapping layout for all blocks (>1MB threshold)

Frame Timer:
- Added event-loop stall detection: measures gaps between consecutive events to catch blocking operations that the input→paint tracker missed