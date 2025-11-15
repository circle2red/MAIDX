"""
MAIDX - Multimodel AI based Data Extraction Tool
Main application entry point
"""
import os
import sys
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow
import dotenv
dotenv.load_dotenv()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("MAIDX")
    app.setOrganizationName("MAIDX")

    window = MainWindow()
    window.show()
    if os.getenv("LLM_MODEL"):
        llm_env = {
            "endpoint": os.getenv("LLM_API"),
            "model": os.getenv("LLM_MODEL"),
            "headers": os.getenv("LLM_HEADERS"),
            "api_key": os.getenv("LLM_KEY")
        }
        window.model_setup_tab.load_model_from_dict(llm_env)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
