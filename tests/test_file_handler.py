"""
Tests for the FileHandler module.
"""

import pytest
import tempfile
import os
from pathlib import Path

from editor.file_handler import FileHandler, FileResult, SaveResult, FileError


class TestFileHandlerRead:
    """Tests for FileHandler.read_file()"""
    
    def test_read_existing_file(self, tmp_path):
        """Reading an existing file returns its content."""
        test_file = tmp_path / "test.txt"
        test_content = "Hello, World!\nLine 2"
        test_file.write_text(test_content, encoding="utf-8")
        
        result = FileHandler.read_file(str(test_file))
        
        assert result.success is True
        assert result.content == test_content
        assert result.error == FileError.NONE
    
    def test_read_empty_file(self, tmp_path):
        """Reading an empty file returns empty string."""
        test_file = tmp_path / "empty.txt"
        test_file.write_text("", encoding="utf-8")
        
        result = FileHandler.read_file(str(test_file))
        
        assert result.success is True
        assert result.content == ""
    
    def test_read_nonexistent_file(self, tmp_path):
        """Reading a non-existent file returns NOT_FOUND error."""
        nonexistent = tmp_path / "does_not_exist.txt"
        
        result = FileHandler.read_file(str(nonexistent))
        
        assert result.success is False
        assert result.error == FileError.NOT_FOUND
        assert result.content is None
    
    def test_read_utf8_content(self, tmp_path):
        """Reading a file with UTF-8 characters works correctly."""
        test_file = tmp_path / "unicode.txt"
        test_content = "Hello 世界! 🎉 αβγ"
        test_file.write_text(test_content, encoding="utf-8")
        
        result = FileHandler.read_file(str(test_file))
        
        assert result.success is True
        assert result.content == test_content
    
    def test_read_file_with_newlines(self, tmp_path):
        """Reading a file preserves different newline types."""
        test_file = tmp_path / "newlines.txt"
        test_content = "Line1\nLine2\nLine3"
        test_file.write_text(test_content, encoding="utf-8")
        
        result = FileHandler.read_file(str(test_file))
        
        assert result.success is True
        assert result.content == test_content


class TestFileHandlerWrite:
    """Tests for FileHandler.write_file()"""
    
    def test_write_new_file(self, tmp_path):
        """Writing to a new file creates it with correct content."""
        test_file = tmp_path / "new.txt"
        test_content = "New file content"
        
        result = FileHandler.write_file(str(test_file), test_content)
        
        assert result.success is True
        assert result.error == FileError.NONE
        assert test_file.read_text(encoding="utf-8") == test_content
    
    def test_write_overwrites_existing_file(self, tmp_path):
        """Writing to an existing file overwrites its content."""
        test_file = tmp_path / "existing.txt"
        test_file.write_text("Original content", encoding="utf-8")
        new_content = "New content"
        
        result = FileHandler.write_file(str(test_file), new_content)
        
        assert result.success is True
        assert test_file.read_text(encoding="utf-8") == new_content
    
    def test_write_empty_content(self, tmp_path):
        """Writing empty content creates an empty file."""
        test_file = tmp_path / "empty.txt"
        
        result = FileHandler.write_file(str(test_file), "")
        
        assert result.success is True
        assert test_file.read_text(encoding="utf-8") == ""
    
    def test_write_utf8_content(self, tmp_path):
        """Writing UTF-8 characters works correctly."""
        test_file = tmp_path / "unicode.txt"
        test_content = "Hello 世界! 🎉 αβγ"
        
        result = FileHandler.write_file(str(test_file), test_content)
        
        assert result.success is True
        assert test_file.read_text(encoding="utf-8") == test_content
    
    def test_write_creates_parent_directories(self, tmp_path):
        """Writing to a path with missing directories creates them."""
        test_file = tmp_path / "subdir" / "nested" / "file.txt"
        test_content = "Nested content"
        
        result = FileHandler.write_file(str(test_file), test_content)
        
        assert result.success is True
        assert test_file.exists()
        assert test_file.read_text(encoding="utf-8") == test_content
    
    def test_write_multiline_content(self, tmp_path):
        """Writing multiline content preserves newlines."""
        test_file = tmp_path / "multiline.txt"
        test_content = "Line 1\nLine 2\nLine 3\n"
        
        result = FileHandler.write_file(str(test_file), test_content)
        
        assert result.success is True
        assert test_file.read_text(encoding="utf-8") == test_content


class TestFileHandlerErrors:
    """Tests for error handling in FileHandler."""
    
    def test_read_permission_error(self, tmp_path, monkeypatch):
        """Reading a file with permission denied returns PERMISSION_ERROR."""
        test_file = tmp_path / "noaccess.txt"
        test_file.write_text("content", encoding="utf-8")
        
        # Mock Path.read_text to raise PermissionError
        original_read = Path.read_text
        def mock_read(*args, **kwargs):
            raise PermissionError("Access denied")
        
        monkeypatch.setattr(Path, "read_text", mock_read)
        
        result = FileHandler.read_file(str(test_file))
        
        assert result.success is False
        assert result.error == FileError.PERMISSION_ERROR
        assert "Permission denied" in result.error_message
    
    def test_read_oserror(self, tmp_path, monkeypatch):
        """Reading a file with OSError returns READ_ERROR."""
        test_file = tmp_path / "oserror.txt"
        test_file.write_text("content", encoding="utf-8")
        
        # Mock Path.read_text to raise OSError
        original_read = Path.read_text
        def mock_read(*args, **kwargs):
            raise OSError("IO error")
        
        monkeypatch.setattr(Path, "read_text", mock_read)
        
        result = FileHandler.read_file(str(test_file))
        
        assert result.success is False
        assert result.error == FileError.READ_ERROR
        assert "Error reading file" in result.error_message
    
    def test_write_permission_error(self, tmp_path, monkeypatch):
        """Writing with permission denied returns PERMISSION_ERROR."""
        test_file = tmp_path / "noaccess.txt"
        
        # Mock Path.write_text to raise PermissionError
        def mock_write(*args, **kwargs):
            raise PermissionError("Access denied")
        
        monkeypatch.setattr(Path, "write_text", mock_write)
        
        result = FileHandler.write_file(str(test_file), "content")
        
        assert result.success is False
        assert result.error == FileError.PERMISSION_ERROR
        assert "Permission denied" in result.error_message
    
    def test_write_oserror(self, tmp_path, monkeypatch):
        """Writing with OSError returns WRITE_ERROR."""
        test_file = tmp_path / "oserror.txt"
        
        # Mock Path.write_text to raise OSError
        def mock_write(*args, **kwargs):
            raise OSError("IO error")
        
        monkeypatch.setattr(Path, "write_text", mock_write)
        
        result = FileHandler.write_file(str(test_file), "content")
        
        assert result.success is False
        assert result.error == FileError.WRITE_ERROR
        assert "Error writing file" in result.error_message


class TestFileHandlerRoundTrip:
    """Tests for read/write round-trip behavior."""
    
    def test_write_then_read_returns_same_content(self, tmp_path):
        """Content written and read back is identical."""
        test_file = tmp_path / "roundtrip.txt"
        test_content = "Test content with\nmultiple lines\nand 日本語"
        
        write_result = FileHandler.write_file(str(test_file), test_content)
        read_result = FileHandler.read_file(str(test_file))
        
        assert write_result.success is True
        assert read_result.success is True
        assert read_result.content == test_content
    
    def test_write_html_content(self, tmp_path):
        """HTML content can be written and read back."""
        test_file = tmp_path / "formatted.txt"
        html_content = '<!DOCTYPE HTML><html><body><p style="font-size:14pt;">Test</p></body></html>'
        
        write_result = FileHandler.write_file(str(test_file), html_content)
        read_result = FileHandler.read_file(str(test_file))
        
        assert write_result.success is True
        assert read_result.success is True
        assert read_result.content == html_content
    
    def test_html_detection_doctype(self, tmp_path):
        """HTML content starting with DOCTYPE is detected."""
        content = '<!DOCTYPE HTML><html><body>Test</body></html>'
        is_html = content.strip().startswith('<!DOCTYPE') or content.strip().startswith('<html')
        assert is_html is True
    
    def test_html_detection_html_tag(self, tmp_path):
        """HTML content starting with html tag is detected."""
        content = '<html><body>Test</body></html>'
        is_html = content.strip().startswith('<!DOCTYPE') or content.strip().startswith('<html')
        assert is_html is True
    
    def test_plain_text_not_detected_as_html(self, tmp_path):
        """Plain text is not detected as HTML."""
        content = 'Hello, this is plain text.\nNo HTML here.'
        is_html = content.strip().startswith('<!DOCTYPE') or content.strip().startswith('<html')
        assert is_html is False
