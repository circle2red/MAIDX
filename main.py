"""
MAIDX - Multimodel AI based Data Extraction Tool
Main application entry point
"""
import sys
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("MAIDX")
    app.setOrganizationName("MAIDX")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
