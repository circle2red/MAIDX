"""
Method Setup Tab - Configure extraction methods and options
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                               QLabel, QCheckBox, QPushButton, QMessageBox)
from PySide6.QtCore import Signal


class MethodSetupTab(QWidget):
    """Tab for configuring extraction methods"""

    method_changed = Signal()

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Extraction Methods Group
        methods_group = QGroupBox("Extraction Methods")
        methods_layout = QVBoxLayout()

        # Vision-based extraction
        self.enable_vision = QCheckBox("Enable Vision-based Extraction")
        self.enable_vision.setChecked(True)
        self.enable_vision.setToolTip("Use AI vision models to extract data from images and PDFs")
        self.enable_vision.stateChanged.connect(self.on_method_changed)
        methods_layout.addWidget(self.enable_vision)

        # Text-based extraction
        self.enable_text = QCheckBox("Enable Text-based Extraction")
        self.enable_text.setChecked(False)
        self.enable_text.setToolTip("Extract text first, then use LLM to parse structured data")
        self.enable_text.stateChanged.connect(self.on_method_changed)
        methods_layout.addWidget(self.enable_text)

        # OCR preprocessing
        self.enable_ocr = QCheckBox("Enable OCR Preprocessing")
        self.enable_ocr.setChecked(False)
        self.enable_ocr.setToolTip("Apply OCR before sending to LLM (useful for scanned documents)")
        self.enable_ocr.stateChanged.connect(self.on_method_changed)
        methods_layout.addWidget(self.enable_ocr)

        methods_group.setLayout(methods_layout)
        layout.addWidget(methods_group)

        # Processing Options Group
        options_group = QGroupBox("Processing Options")
        options_layout = QVBoxLayout()

        # Batch processing
        self.enable_batch = QCheckBox("Enable Batch Processing")
        self.enable_batch.setChecked(True)
        self.enable_batch.setToolTip("Process multiple files in parallel")
        self.enable_batch.stateChanged.connect(self.on_method_changed)
        options_layout.addWidget(self.enable_batch)

        # Auto-validation
        self.enable_validation = QCheckBox("Enable Auto-validation")
        self.enable_validation.setChecked(True)
        self.enable_validation.setToolTip("Automatically validate extracted data against schema")
        self.enable_validation.stateChanged.connect(self.on_method_changed)
        options_layout.addWidget(self.enable_validation)

        # Retry on failure
        self.enable_retry = QCheckBox("Enable Retry on Failure")
        self.enable_retry.setChecked(True)
        self.enable_retry.setToolTip("Retry extraction if validation fails")
        self.enable_retry.stateChanged.connect(self.on_method_changed)
        options_layout.addWidget(self.enable_retry)

        options_group.setLayout(options_layout)
        layout.addWidget(options_group)

        # Output Options Group
        output_group = QGroupBox("Output Options")
        output_layout = QVBoxLayout()

        # Save intermediate results
        self.save_intermediate = QCheckBox("Save Intermediate Results")
        self.save_intermediate.setChecked(False)
        self.save_intermediate.setToolTip("Save intermediate processing steps for debugging")
        self.save_intermediate.stateChanged.connect(self.on_method_changed)
        output_layout.addWidget(self.save_intermediate)

        # Pretty print JSON
        self.pretty_json = QCheckBox("Pretty Print JSON Output")
        self.pretty_json.setChecked(True)
        self.pretty_json.setToolTip("Format JSON output with indentation")
        self.pretty_json.stateChanged.connect(self.on_method_changed)
        output_layout.addWidget(self.pretty_json)

        output_group.setLayout(output_layout)
        layout.addWidget(output_group)

        # Reset to defaults button
        reset_layout = QHBoxLayout()
        reset_layout.addStretch()
        self.reset_btn = QPushButton("Reset to Defaults")
        self.reset_btn.clicked.connect(self.reset_to_defaults)
        reset_layout.addWidget(self.reset_btn)
        layout.addLayout(reset_layout)

        layout.addStretch()

    def on_method_changed(self):
        """Handle method option changes"""
        self.method_changed.emit()

    def reset_to_defaults(self):
        """Reset all options to default values"""
        self.enable_vision.setChecked(True)
        self.enable_text.setChecked(False)
        self.enable_ocr.setChecked(False)
        self.enable_batch.setChecked(True)
        self.enable_validation.setChecked(True)
        self.enable_retry.setChecked(True)
        self.save_intermediate.setChecked(False)
        self.pretty_json.setChecked(True)

        QMessageBox.information(self, "Reset", "All options have been reset to defaults.")
        self.method_changed.emit()

    def get_config(self):
        """Get the current method configuration"""
        config = {
            # Extraction Methods
            "enable_vision": self.enable_vision.isChecked(),
            "enable_text": self.enable_text.isChecked(),
            "enable_ocr": self.enable_ocr.isChecked(),

            # Processing Options
            "enable_batch": self.enable_batch.isChecked(),
            "enable_validation": self.enable_validation.isChecked(),
            "enable_retry": self.enable_retry.isChecked(),

            # Output Options
            "save_intermediate": self.save_intermediate.isChecked(),
            "pretty_json": self.pretty_json.isChecked()
        }

        return config
