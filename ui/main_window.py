"""
Main window with tab interface
"""
from PySide6.QtWidgets import QMainWindow, QTabWidget, QWidget, QVBoxLayout
from ui.tabs.model_setup_tab import ModelSetupTab
from ui.tabs.schema_setup_tab import SchemaSetupTab
from ui.tabs.method_setup_tab import MethodSetupTab
from ui.tabs.data_extraction_tab import DataExtractionTab


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MAIDX - Multimodel AI Data Extraction")
        self.setMinimumSize(900, 600)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Create main layout
        layout = QVBoxLayout(central_widget)

        # Create tab widget
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Create tabs
        self.model_setup_tab = ModelSetupTab()
        self.schema_setup_tab = SchemaSetupTab()
        self.method_setup_tab = MethodSetupTab()
        self.data_extraction_tab = DataExtractionTab()

        # Add tabs
        self.tabs.addTab(self.model_setup_tab, "Model Setup")
        self.tabs.addTab(self.schema_setup_tab, "Schema Setup")
        self.tabs.addTab(self.method_setup_tab, "Method Setup")
        self.tabs.addTab(self.data_extraction_tab, "Data Extraction")

        # Connect tabs to share data
        self.schema_setup_tab.set_model_tab(self.model_setup_tab)
        self.data_extraction_tab.set_model_tab(self.model_setup_tab)
        self.data_extraction_tab.set_schema_tab(self.schema_setup_tab)
        self.data_extraction_tab.set_method_tab(self.method_setup_tab)
