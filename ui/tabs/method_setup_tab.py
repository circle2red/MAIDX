"""
Method Setup Tab - Configure extraction methods and options
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                               QLabel, QCheckBox, QPushButton, QMessageBox, QButtonGroup, QRadioButton, QLineEdit)
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
        pdf_group = QGroupBox("PDF Processing Methods")
        pdf_layout = QVBoxLayout()

        # Vision-based extraction
        self.pdf_mode_group = QButtonGroup(self)
        self.pdf_pure_text_extraction = QRadioButton("Pure Text Extraction")
        self.pdf_pure_text_extraction.setChecked(True)
        self.pdf_mode_group.addButton(self.pdf_pure_text_extraction)
        pdf_layout.addWidget(self.pdf_pure_text_extraction)

        self.pdf_text_with_img = QRadioButton("Text Extraction + Image")
        self.pdf_mode_group.addButton(self.pdf_text_with_img)
        pdf_layout.addWidget(self.pdf_text_with_img)

        self.pdf_page_as_img = QRadioButton("Page as Image")
        self.pdf_mode_group.addButton(self.pdf_page_as_img)
        pdf_layout.addWidget(self.pdf_page_as_img)

        pdf_group.setLayout(pdf_layout)
        layout.addWidget(pdf_group)

        # Segmentation Options Group
        segmentation_group = QGroupBox("Segmentation Options")
        segmentation_layout = QVBoxLayout()

        self.enable_seg = QCheckBox("Use segmentation (multiple rounds of chat per file)")
        self.enable_seg.setChecked(True)
        segmentation_layout.addWidget(self.enable_seg)

        row1 = QHBoxLayout()
        self.seg_max_text_len = QLineEdit()
        self.seg_max_text_len.setText("30000")
        row1.addWidget(QLabel("Max text length: "))
        row1.addWidget(self.seg_max_text_len)

        self.seg_max_img = QLineEdit()
        self.seg_max_img.setText("1")
        row1.addWidget(QLabel("Max image count: "))
        row1.addWidget(self.seg_max_img)

        self.seg_text_overlap = QLineEdit()
        self.seg_text_overlap.setText("1000")
        row1.addWidget(QLabel("Text overlapping length: "))
        row1.addWidget(self.seg_text_overlap)

        segmentation_layout.addLayout(row1)

        segmentation_group.setLayout(segmentation_layout)
        layout.addWidget(segmentation_group)

        self.enable_multi = QCheckBox("Multiple objects per file")
        self.enable_multi.setChecked(False)
        segmentation_layout.addWidget(self.enable_multi)

        # Tool Options Group
        tool_group = QGroupBox("Tool Options")
        tool_layout = QVBoxLayout()

        # Save intermediate results
        self.tool_python = QCheckBox("Restricted Python Tool")
        self.tool_python.setChecked(True)
        tool_layout.addWidget(self.tool_python)

        self.tool_web_fetch = QCheckBox("Web Fetch Tool")
        self.tool_web_fetch.setChecked(True)
        tool_layout.addWidget(self.tool_web_fetch)

        # self.tool_web_search = QCheckBox("Web Search Tool")
        # self.tool_web_search.setChecked(True)
        # tool_layout.addWidget(self.tool_web_search)

        tool_group.setLayout(tool_layout)
        layout.addWidget(tool_group)

        layout.addStretch()

    def get_config(self):
        """Get the current method configuration"""

        def as_int(x, default=0):
            try:
                return int(x)
            except ValueError:
                return default

        if self.pdf_pure_text_extraction.isChecked():
            pdf_mode = "text"
        elif self.pdf_text_with_img.isChecked():
            pdf_mode = "text_with_img"
        else:
            pdf_mode = "page_as_img"

        use_segmentation = self.enable_seg.isChecked()
        max_text_length = as_int(self.seg_max_text_len.text(), 30000)
        max_img_count = as_int(self.seg_max_img.text(), 1)
        overlapping_text_length = as_int(self.seg_text_overlap, 1000)
        multi_obj = self.enable_multi.isChecked()

        python_tool = self.tool_python.isChecked()
        web_fetch_tool = self.tool_web_fetch.isChecked()

        config = {
            "pdf_mode": pdf_mode,
            "use_segmentation": use_segmentation,
            "max_text_length": max_text_length,
            "max_img_count": max_img_count,
            "overlapping_text_length": overlapping_text_length,
            "multi_obj": multi_obj,
            "python_tool": python_tool,
            "web_fetch_tool": web_fetch_tool,
        }

        return config
