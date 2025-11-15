"""
Data Extraction Tab - Import files and extract data
"""
from pathlib import Path

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                               QLabel, QPushButton, QLineEdit, QRadioButton,
                               QProgressBar, QTextEdit, QFileDialog, QMessageBox,
                               QButtonGroup, QCheckBox)
from PySide6.QtCore import Qt, QThread, Signal
import os
from core.extraction_thread import ExtractionThread


class DataExtractionTab(QWidget):
    """Tab for importing files and extracting data"""

    def __init__(self):
        super().__init__()
        self.save_log = None
        self.model_tab = None
        self.schema_tab = None
        self.method_tab = None
        self.extraction_thread = None
        self.init_ui()

    def set_model_tab(self, model_tab):
        """Set reference to model setup tab"""
        self.model_tab = model_tab

    def set_schema_tab(self, schema_tab):
        """Set reference to schema setup tab"""
        self.schema_tab = schema_tab

    def set_method_tab(self, method_tab):
        """Set reference to method setup tab"""
        self.method_tab = method_tab

    def init_ui(self):
        layout = QVBoxLayout(self)

        # File Import Group
        import_group = QGroupBox("File Import")
        import_layout = QVBoxLayout()

        # Folder selection
        folder_layout = QHBoxLayout()
        folder_layout.addWidget(QLabel("Input Folder:"))
        self.folder_input = QLineEdit()
        self.folder_input.setPlaceholderText("Select folder containing files to process...")
        self.folder_input.setReadOnly(True)
        folder_layout.addWidget(self.folder_input)

        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self.browse_folder)
        folder_layout.addWidget(self.browse_btn)

        import_layout.addLayout(folder_layout)

        # File count display
        self.file_count_label = QLabel("No files selected")
        import_layout.addWidget(self.file_count_label)

        import_group.setLayout(import_layout)
        layout.addWidget(import_group)

        # Output Settings Group
        output_group = QGroupBox("Output Settings")
        output_layout = QVBoxLayout()

        output_file_layout = QHBoxLayout()
        output_file_layout.addWidget(QLabel("Output Folder:"))
        self.output_folder_input = QLineEdit()
        self.output_folder_input.setPlaceholderText("JSON output path")
        output_file_layout.addWidget(self.output_folder_input)

        self.output_browse_btn = QPushButton("Browse...")
        self.output_browse_btn.clicked.connect(self.browse_output)
        output_file_layout.addWidget(self.output_browse_btn)

        output_layout.addLayout(output_file_layout)

        output_log_layout = QHBoxLayout()
        self.log_raw = QCheckBox("Log raw requests and responses")
        output_log_layout.addWidget(self.log_raw)
        output_layout.addLayout(output_log_layout)

        output_group.setLayout(output_layout)
        layout.addWidget(output_group)

        # Progress Group
        progress_group = QGroupBox("Extraction Progress")
        progress_layout = QVBoxLayout()

        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        progress_layout.addWidget(self.progress_bar)

        self.status_label = QLabel("Ready to start extraction")
        progress_layout.addWidget(self.status_label)

        # Log output
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        progress_layout.addWidget(QLabel("Log:"))
        progress_layout.addWidget(self.log_text)

        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)

        # Control Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.start_btn = QPushButton("Start Extraction")
        self.start_btn.clicked.connect(self.start_extraction)
        self.start_btn.setMinimumWidth(150)
        btn_layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self.stop_extraction)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setMinimumWidth(150)
        btn_layout.addWidget(self.stop_btn)

        layout.addLayout(btn_layout)

        # DEBUG todo
        self.test = QPushButton("test")
        self.test.clicked.connect(self.get_config)
        btn_layout.addWidget(self.test)

        layout.addStretch()

    def browse_folder(self):
        """Browse for input folder"""
        folder = QFileDialog.getExistingDirectory(self, "Select Input Folder")
        if folder:
            self.folder_input.setText(folder)
            self.update_files_to_extract(folder)

    def update_files_to_extract(self, folder):
        """Update the files to extract"""
        supported_extensions = ['.txt', '.pdf', '.jpg', '.jpeg', '.png']
        files = []
        for filename in os.listdir(folder):
            full_path = Path(folder) / filename
            if full_path.is_file():
                ext = os.path.splitext(full_path)[1].lower()
                if ext in supported_extensions:
                    files.append(str(full_path.absolute()))

        self.file_count_label.setText(f"Found {len(files)} supported files")
        self.files_to_process = files

    def browse_output(self):
        """Browse for output directory"""
        filename = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if filename:
            self.output_folder_input.setText(filename)

    def get_config(self):
        config = {
            "files": self.files_to_process,  # list of file paths
            "output_folder": self.output_folder_input.text(),  # str folder
            "log_raw": self.log_raw.isChecked(),  # True/False
        }
        return config

    def start_extraction(self):
        """Start the data extraction process"""
        # Validate inputs
        if not self.folder_input.text():
            QMessageBox.warning(self, "No Input", "Please select an input folder.")
            return

        if not hasattr(self, 'files_to_process') or not self.files_to_process:
            QMessageBox.warning(self, "No Files", "No supported files found in the selected folder.")
            return

        if not self.output_folder_input.text():
            QMessageBox.warning(self, "No Output", "Please specify an output file.")
            return

        if not self.model_tab:
            QMessageBox.warning(self, "Error", "Model configuration not available.")
            return

        if not self.schema_tab:
            QMessageBox.warning(self, "Error", "Schema configuration not available.")
            return

        # Get configurations
        model_config = self.model_tab.get_config()
        schema_config = self.schema_tab.get_config()

        # Validate model config
        if not model_config['endpoint'] or not model_config['model']:
            QMessageBox.warning(self, "Invalid Model", "Please configure the model in the Model Setup tab.")
            return

        # Validate schema config
        if not schema_config['fields'] and not schema_config['raw_schema']:
            QMessageBox.warning(self, "Invalid Schema", "Please define a schema in the Schema Setup tab.")
            return

        # Start extraction thread
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.setValue(0)
        self.log_text.clear()
        self.add_log("Starting extraction process...")

        self.extraction_thread = ExtractionThread(
            model_config=self.model_tab.get_config(),
            schema_config=self.schema_tab.get_config(),
            method_config=self.method_tab.get_config(),
            extraction_config=self.get_config(),
        )

        self.extraction_thread.progress.connect(self.update_progress)
        self.extraction_thread.log.connect(self.add_log)
        self.extraction_thread.finished.connect(self.extraction_finished)
        self.extraction_thread.error.connect(self.extraction_error)

        self.extraction_thread.start()

    def stop_extraction(self):
        """Stop the extraction process"""
        if self.extraction_thread and self.extraction_thread.isRunning():
            self.extraction_thread.stop()
            self.add_log("Stopping extraction...")

    def update_progress(self, current, total):
        """Update progress bar"""
        percentage = int((current / total) * 100) if total > 0 else 0
        self.progress_bar.setValue(percentage)
        self.status_label.setText(f"Processing file {current} of {total}")

    def add_log(self, message):
        """Add message to log"""
        self.log_text.append(message)

    def extraction_finished(self):
        """Handle extraction completion"""
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setValue(100)
        self.status_label.setText("Extraction completed!")
        self.add_log("Extraction finished successfully.")
        QMessageBox.information(self, "Complete", "Data extraction completed successfully!")

    def extraction_error(self, error_msg):
        """Handle extraction error"""
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_label.setText("Error occurred")
        self.add_log(f"ERROR: {error_msg}")
        QMessageBox.critical(self, "Error", f"An error occurred:\n{error_msg}")
