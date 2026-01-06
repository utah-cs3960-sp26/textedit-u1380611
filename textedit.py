"""
Text Editor Application - Main Entry Point

A native, cross-platform text editor using Qt (PySide6).
"""

import sys
from PySide6.QtWidgets import QApplication
from editor.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("TextEdit")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
