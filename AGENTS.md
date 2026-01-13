# Agent Instructions

## Testing Requirements

**Before reporting back to the user, you MUST:**

1. **Add sufficient tests** for any changes made:
   - New features require comprehensive test coverage
   - Bug fixes require regression tests
   - UI changes require tests for the underlying logic
   - Place tests in the appropriate file under `tests/`

2. **Run ALL tests** and ensure they pass:
   ```bash
   python -m pytest tests/ -v
   ```

3. **Fix all bugs** discovered during testing before reporting completion

## Project Structure

- `editor/` - Main application modules
- `tests/` - Test files (pytest)
- `textedit.py` - Application entry point

## Commands

- **Run tests**: `python -m pytest tests/ -v`
- **Run app**: `python textedit.py`
- **Check types**: The project uses PySide6 (Qt bindings)

## Test File Mapping

| Module | Test File |
|--------|-----------|
| `editor/document.py` | `tests/test_document.py` |
| `editor/editor_widget.py` | `tests/test_editor_state.py` |
| `editor/file_handler.py` | `tests/test_file_handler.py` |
| `editor/editor_pane.py` | `tests/test_tabs.py` |
| `editor/split_container.py` | `tests/test_tabs.py` |
| `editor/tab_bar.py` | `tests/test_tab_bar.py` |
| `editor/theme_manager.py` | `tests/test_theme.py` |

## Testing Conventions

- Use pytest fixtures for Qt widgets (see `conftest.py`)
- Session-scoped `qapp` fixture for QApplication
- Clean up widgets with `deleteLater()` in fixtures
- Group related tests in classes (e.g., `TestDocumentCreation`)
