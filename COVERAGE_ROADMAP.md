# Code Coverage Improvement Roadmap

**Current Status: 64% Overall Coverage (336 tests)**

## Completed Modules ✅

1. ✅ **editor/__init__.py** - 100%
2. ✅ **editor/document.py** - 100% (added 4 tests for property setters)
3. ✅ **editor/editor_widget.py** - 100% (added 1 test for file_path setter)
4. ✅ **editor/file_handler.py** - 100% (added 5 tests for error handling)
5. ✅ **editor/find_replace.py** - 99% (1 line unreachable: defensive code at line 350)

## Modules Requiring Work for 95%+ Coverage

### Priority 1: Quick Wins (5-15 lines each)

#### 1. theme_manager.py (91% → 100%)
**Missing 11 lines:** 1680-1681, 1691-1692, 1700-1701, 1724, 1738-1739, 1751-1752
- **Effort:** 30 minutes
- **Test file:** tests/test_theme.py
- Add tests for:
  - Custom theme saving/loading paths (lines 1738-1752)
  - Edge cases in theme application
- **Estimated new tests:** 5-8

#### 2. file_tree.py (87% → 95%+)
**Missing 27 lines:** 103, 116, 131, 268-276, 280, 284, 288-295, 299-306, 321-328
- **Effort:** 45 minutes
- **Test file:** tests/test_file_tree.py
- Add tests for:
  - Double-click handling on files/folders (lines 103, 116, 131)
  - Right-click context menu handlers (lines 268-306)
  - Selection changed callbacks (lines 321-328)
- **Estimated new tests:** 8-12

#### 3. line_number_editor.py (72% → 85%+)
**Missing 23 lines:** 23, 73, 82-85, 106-136
- **Effort:** 45 minutes
- **Test file:** tests/test_line_numbers.py
- Add tests for:
  - Margin area styling (lines 106-136)
  - Line number painting/rendering (lines 82-85)
  - Font changes (lines 23, 73)
- **Estimated new tests:** 6-10

### Priority 2: Medium Effort (30-50 lines each)

#### 4. font_toolbar.py (65% → 85%+)
**Missing 50 lines:** 34-36, 122-123, 132, 135-136, 175-199, 203-205, 209-211, 215-234, 256-259
- **Effort:** 60 minutes
- **Test file:** tests/test_font_toolbar.py
- Add tests for:
  - Font selection combobox behavior (lines 175-199, 215-234)
  - Size spinbox handling (lines 203-211)
  - Font updates on editor change (lines 256-259)
- **Estimated new tests:** 10-15

#### 5. editor_pane.py (80% → 90%+)
**Missing 42 lines:** 88, 140-141, 152-167, 177-181, 196-199, 267, 273, 283, 307, 315, 319-328, 333, 336, 338, 347
- **Effort:** 90 minutes
- **Test file:** tests/test_tabs.py
- Add tests for:
  - Document tab operations (lines 140-199)
  - Tab signals and state changes (lines 267, 273, 283, 307, 315)
  - Context menu handling (lines 319-347)
- **Estimated new tests:** 15-20

### Priority 3: Heavy Lift (75+ lines each)

#### 6. split_container.py (61% → 85%+)
**Missing 109 lines:** Large ranges for split/merge/swap operations
- **Effort:** 120 minutes
- **Test file:** tests/test_tabs.py  
- Add tests for all split/merge scenarios, pane interactions
- **Estimated new tests:** 20-30

#### 7. settings_dialog.py (74% → 90%+)
**Missing 100 lines:** Theme customization, settings panels
- **Effort:** 90 minutes
- **Test file:** tests/test_settings_dialog.py
- Add tests for dialog interactions, theme editing
- **Estimated new tests:** 15-20

#### 8. tab_bar.py (49% → 85%+)
**Missing 79 lines:** Most of the custom tab bar implementation
- **Effort:** 120 minutes
- **Test file:** tests/test_tab_bar.py
- Add tests for tab manipulation, drag/drop, context menus
- **Estimated new tests:** 20-30

### Priority 4: Out of Scope for Now

#### main_window.py (0%)
**Missing:** All 553 lines
- **Effort:** 8+ hours (requires comprehensive UI testing)
- **Status:** DEFER - This requires extensive integration testing and main window lifecycle testing
- **Alternative:** Focus on unit tests for imported modules instead

---

## Execution Strategy

### Phase 1: Quick Wins (2-3 hours)
- Complete: theme_manager.py, file_tree.py, line_number_editor.py
- **Target Coverage:** 72% overall

### Phase 2: Medium Effort (2-3 hours)
- Complete: font_toolbar.py, editor_pane.py
- **Target Coverage:** 78-80% overall

### Phase 3: Heavy Lift (4-5 hours)
- Complete: split_container.py, settings_dialog.py, tab_bar.py
- **Target Coverage:** 85-90% overall

---

## Test Writing Guidelines

For each module, follow this pattern:
1. Run coverage report to see missing lines
2. Understand what code paths those lines represent
3. Write minimal tests that trigger those paths
4. Verify coverage increase
5. Commit tests

## Command Reference

```bash
# Run with coverage for specific module
python -m pytest tests/test_MODULE.py -v --cov=editor.MODULE --cov-report=term-missing

# Run all tests with full project coverage
python -m pytest tests/ --cov=editor --cov-report=term-missing -q

# Generate HTML report
python -m pytest tests/ --cov=editor --cov-report=html
# Then open: htmlcov/index.html
```

---

## Current Stats

| Module | Lines | Miss | Coverage | Status |
|--------|-------|------|----------|--------|
| __init__.py | 0 | 0 | 100% | ✅ DONE |
| document.py | 85 | 0 | 100% | ✅ DONE |
| editor_widget.py | 68 | 0 | 100% | ✅ DONE |
| file_handler.py | 46 | 0 | 100% | ✅ DONE |
| find_replace.py | 391 | 1 | 99% | ✅ DONE (unreachable) |
| theme_manager.py | 128 | 11 | 91% | 🔷 NEXT |
| file_tree.py | 202 | 27 | 87% | 🔷 NEXT |
| editor_pane.py | 215 | 42 | 80% | 📋 MEDIUM |
| line_number_editor.py | 81 | 23 | 72% | 📋 MEDIUM |
| settings_dialog.py | 384 | 100 | 74% | 📋 MEDIUM |
| font_toolbar.py | 143 | 50 | 65% | 📋 MEDIUM |
| split_container.py | 277 | 109 | 61% | 📋 MEDIUM |
| tab_bar.py | 154 | 79 | 49% | 📋 MEDIUM |
| main_window.py | 553 | 553 | 0% | ⛔ DEFER |
|---------|--------|--------|--------|--------|
| **TOTAL** | **2727** | **995** | **64%** | 📊 |

