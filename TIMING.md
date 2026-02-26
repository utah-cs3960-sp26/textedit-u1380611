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