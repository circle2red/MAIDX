"""
Method Setup Tab - Configure extraction methods and options
"""
from typing import Literal

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                               QLabel, QCheckBox, QPushButton, QMessageBox, QButtonGroup, QRadioButton, QLineEdit,
                               QTextEdit)
from PySide6.QtCore import Signal


class MethodSetupTab(QWidget):
    """Tab for configuring extraction methods"""

    method_changed = Signal()

    def __init__(self):
        super().__init__()
        self.init_ui()

    def set_default_segment_value(self, mode: Literal['img', 'txt']):
        if mode == 'img':
            self.seg_max_text_len.setText("")
            self.seg_max_pages.setText("5")
            self.seg_overlap.setText("1")
        else:
            self.seg_max_text_len.setText("30000")
            self.seg_max_pages.setText("")
            self.seg_overlap.setText("1000")


    def init_ui(self):
        layout = QVBoxLayout(self)

        # Extraction Methods Group
        pdf_group = QGroupBox("PDF Processing Methods")
        pdf_layout = QVBoxLayout()

        # Vision-based extraction
        self.pdf_mode_group = QButtonGroup(self)

        self.pdf_pure_text_extraction = QRadioButton("Pure Text Extraction")
        self.pdf_pure_text_extraction.setChecked(True)
        self.pdf_pure_text_extraction.toggled.connect(
            lambda checked: self.set_default_segment_value(mode='txt') if checked else None
        )
        self.pdf_mode_group.addButton(self.pdf_pure_text_extraction)
        pdf_layout.addWidget(self.pdf_pure_text_extraction)

        self.pdf_text_with_img = QRadioButton("Text Extraction + Image (Forced Segmentation by Page, *)")
        self.pdf_text_with_img.toggled.connect(
            lambda checked: self.set_default_segment_value(mode='img') if checked else None
        )
        self.pdf_mode_group.addButton(self.pdf_text_with_img)
        pdf_layout.addWidget(self.pdf_text_with_img)

        self.pdf_page_as_img = QRadioButton("Page as Image (Forced Segmentation by Page, *)")
        self.pdf_page_as_img.toggled.connect(
            lambda checked: self.set_default_segment_value(mode='img') if checked else None
        )
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

        row = QHBoxLayout()
        self.seg_max_text_len = QLineEdit()
        self.seg_max_text_len.setText("30000")
        row.addWidget(QLabel("Max text length per segment: "))
        row.addWidget(self.seg_max_text_len)

        self.seg_max_pages = QLineEdit()
        self.seg_max_pages.setText("1")
        row.addWidget(QLabel("Max pages count (*): "))
        row.addWidget(self.seg_max_pages)

        self.seg_overlap = QLineEdit()
        self.seg_overlap.setText("1000")
        row.addWidget(QLabel("Text / Page(*) overlapping length: "))
        row.addWidget(self.seg_overlap)

        segmentation_layout.addLayout(row)

        segmentation_group.setLayout(segmentation_layout)
        layout.addWidget(segmentation_group)

        self.enable_multi = QCheckBox("Multiple objects per file")
        self.enable_multi.setChecked(False)
        segmentation_layout.addWidget(self.enable_multi)

        # Tool Options Group
        tool_group = QGroupBox("Tool Options")
        tool_layout = QVBoxLayout()

        # Restricted Python tool
        row = QHBoxLayout()
        self.tool_python = QCheckBox("Restricted Python Tool")
        self.tool_python.setChecked(True)
        row.addWidget(self.tool_python)

        self.tool_python_max_call = QLineEdit()
        self.tool_python_max_call.setText("10")
        row.addWidget(QLabel("Max Python calls per file: "))
        row.addWidget(self.tool_python_max_call)

        tool_layout.addLayout(row)

        # Web fetch tool
        row = QHBoxLayout()
        self.tool_web_fetch = QCheckBox("Web Fetch Tool")
        self.tool_web_fetch.setChecked(True)
        row.addWidget(self.tool_web_fetch)

        self.tool_web_fetch_max_call = QLineEdit()
        self.tool_web_fetch_max_call.setText("10")
        row.addWidget(QLabel("Max web fetch calls per file: "))
        row.addWidget(self.tool_web_fetch_max_call)

        tool_layout.addLayout(row)

        # Think tool
        row = QHBoxLayout()
        self.tool_think = QCheckBox("Internal Think Tool")
        self.tool_think.setChecked(True)
        row.addWidget(self.tool_think)

        self.tool_think_max_call = QLineEdit()
        self.tool_think_max_call.setText("10")
        row.addWidget(QLabel("Max internal thoughts per file: "))
        row.addWidget(self.tool_think_max_call)

        tool_layout.addLayout(row)

        # self.tool_web_search = QCheckBox("Web Search Tool")
        # self.tool_web_search.setChecked(True)
        # tool_layout.addWidget(self.tool_web_search)

        col = QVBoxLayout()
        self.tools_prompt_input = QTextEdit()
        self.tools_prompt_input.setText("If you need to perform calculations or conversions, "
                                        "use the execute_python tool. \n"
                                        "If you want to query the latest news, "
                                        "query https://feeds.bbci.co.uk/news/world/rss.xml using "
                                        "the web_fetch tool.\n"
                                        "Think before you answer.\n")
        col.addWidget(QLabel("Tools prompt:"))
        col.addWidget(self.tools_prompt_input)
        tool_layout.addLayout(col)

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
        max_pages_count = as_int(self.seg_max_pages.text(), 1)
        overlapping_length = as_int(self.seg_overlap.text(), 1000)
        multi_obj = self.enable_multi.isChecked()

        if self.tool_python.isChecked():
            max_python_call = as_int(self.tool_python_max_call.text(), 10)
        else:
            max_python_call = 0

        if self.tool_web_fetch.isChecked():
            max_web_fetch_call = as_int(self.tool_web_fetch_max_call.text(), 10)
        else:
            max_web_fetch_call = 0

        tool_prompt = self.tools_prompt_input.toPlainText()

        config = {
            "pdf_mode": pdf_mode,
            "use_segmentation": use_segmentation,
            "max_text_length": max_text_length,
            "max_pages_count": max_pages_count,
            "overlapping_length": overlapping_length,
            "multi_obj": multi_obj,
            "max_python_call": max_python_call,
            "max_web_fetch_call": max_web_fetch_call,
            "tool_prompt": tool_prompt,
        }

        return config
