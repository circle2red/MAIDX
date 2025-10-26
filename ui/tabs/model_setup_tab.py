"""
Model Setup Tab - Configure LLM model and parameters
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                               QLabel, QComboBox, QLineEdit, QPushButton,
                               QDoubleSpinBox, QSpinBox, QTextEdit, QCheckBox,
                               QFormLayout)
from PySide6.QtCore import Signal


class ModelSetupTab(QWidget):
    """Tab for configuring the LLM model and parameters"""

    model_changed = Signal()

    # Preset configurations
    PRESETS = {
        "GPT-4": {
            "endpoint": "https://api.openai.com/v1/chat/completions",
            "model": "gpt-4-turbo-preview",
            "headers": {"Authorization": "Bearer YOUR_API_KEY", "Content-Type": "application/json"}
        },
        "GPT-3.5": {
            "endpoint": "https://api.openai.com/v1/chat/completions",
            "model": "gpt-3.5-turbo",
            "headers": {"Authorization": "Bearer YOUR_API_KEY", "Content-Type": "application/json"}
        },
        "DeepSeek": {
            "endpoint": "https://api.deepseek.com/v1/chat/completions",
            "model": "deepseek-chat",
            "headers": {"Authorization": "Bearer YOUR_API_KEY", "Content-Type": "application/json"}
        },
        "Grok": {
            "endpoint": "https://api.x.ai/v1/chat/completions",
            "model": "grok-4-fast",
            "headers": {"Authorization": "Bearer YOUR_API_KEY", "Content-Type": "application/json"}
        },
        "Custom": {
            "endpoint": "",
            "model": "",
            "headers": {"Content-Type": "application/json"}
        }
    }

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Model Selection Group
        model_group = QGroupBox("Model Selection")
        model_layout = QFormLayout()

        # Preset selector
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(list(self.PRESETS.keys()))
        self.preset_combo.currentTextChanged.connect(self.on_preset_changed)
        model_layout.addRow("Preset:", self.preset_combo)

        # Endpoint URL
        self.endpoint_input = QLineEdit()
        self.endpoint_input.setPlaceholderText("https://api.example.com/v1/chat/completions")
        model_layout.addRow("Endpoint URL:", self.endpoint_input)

        # Model name
        self.model_input = QLineEdit()
        self.model_input.setPlaceholderText("model-name")
        model_layout.addRow("Model Name:", self.model_input)

        # API Key
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("Your API Key")
        self.api_key_input.setEchoMode(QLineEdit.Password)
        model_layout.addRow("API Key:", self.api_key_input)

        # Custom Headers
        self.headers_input = QTextEdit()
        self.headers_input.setPlaceholderText('{"Header-Name": "Header-Value"}')
        self.headers_input.setMaximumHeight(80)
        model_layout.addRow("Custom Headers (JSON):", self.headers_input)

        model_group.setLayout(model_layout)
        layout.addWidget(model_group)

        # Model Parameters Group
        params_group = QGroupBox("Model Parameters")
        params_layout = QFormLayout()

        # Temperature
        self.temperature_spin = QDoubleSpinBox()
        self.temperature_spin.setRange(0.0, 2.0)
        self.temperature_spin.setSingleStep(0.1)
        self.temperature_spin.setValue(0.7)
        params_layout.addRow("Temperature:", self.temperature_spin)

        # Max Tokens
        self.max_tokens_spin = QSpinBox()
        self.max_tokens_spin.setRange(1, 128000)
        self.max_tokens_spin.setValue(4096)
        params_layout.addRow("Max Tokens:", self.max_tokens_spin)

        # Top P
        self.top_p_spin = QDoubleSpinBox()
        self.top_p_spin.setRange(0.0, 1.0)
        self.top_p_spin.setSingleStep(0.1)
        self.top_p_spin.setValue(1.0)
        params_layout.addRow("Top P:", self.top_p_spin)

        params_group.setLayout(params_layout)
        layout.addWidget(params_group)

        # Tool Use Group
        tools_group = QGroupBox("Tool Configuration")
        tools_layout = QVBoxLayout()

        # Enable Python tool
        self.enable_python_tool = QCheckBox("Enable Safe Python Execution Tool")
        self.enable_python_tool.setChecked(True)
        tools_layout.addWidget(self.enable_python_tool)

        # Future tools placeholder
        future_label = QLabel("(Additional tools can be added here in the future)")
        future_label.setStyleSheet("color: gray; font-style: italic;")
        tools_layout.addWidget(future_label)

        tools_group.setLayout(tools_layout)
        layout.addWidget(tools_group)

        # Test Connection Button
        test_btn_layout = QHBoxLayout()
        test_btn_layout.addStretch()
        self.test_btn = QPushButton("Test Connection")
        self.test_btn.clicked.connect(self.test_connection)
        test_btn_layout.addWidget(self.test_btn)
        layout.addLayout(test_btn_layout)

        layout.addStretch()

        # Load default preset
        self.on_preset_changed(self.preset_combo.currentText())

    def on_preset_changed(self, preset_name):
        """Update fields when preset is changed"""
        if preset_name in self.PRESETS:
            preset = self.PRESETS[preset_name]
            self.endpoint_input.setText(preset["endpoint"])
            self.model_input.setText(preset["model"])

            # Enable/disable custom fields
            is_custom = preset_name == "Custom"
            self.endpoint_input.setEnabled(is_custom or True)
            self.model_input.setEnabled(is_custom or True)

            self.model_changed.emit()

    def test_connection(self):
        """Test the API connection"""
        from PySide6.QtWidgets import QMessageBox
        from core.llm_client import LLMClient
        try:
            client = LLMClient(config=self.get_config())
            resp = client.call(
                system_prompt="You are a helpful assistant.",
                user_prompt="Say Hello World and nothing else."
            )
            QMessageBox.information(self, "Test Connection",
                                    f"Successful: Response with Hello World Request: {resp['content']}")
        except Exception as e:
            QMessageBox.warning(self, "Test Connection", f"Failure: {e}")

    def get_config(self):
        """Get the current model configuration"""
        import json

        # Parse custom headers
        try:
            custom_headers = json.loads(self.headers_input.toPlainText() or "{}")
        except:
            custom_headers = {}

        # Build headers
        headers = {"Content-Type": "application/json"}
        if self.api_key_input.text():
            headers["Authorization"] = f"Bearer {self.api_key_input.text().strip()}"
        headers.update(custom_headers)

        return {
            "endpoint": self.endpoint_input.text(),
            "model": self.model_input.text(),
            "api_key": self.api_key_input.text(),
            "headers": headers,
            "temperature": self.temperature_spin.value(),
            "max_tokens": self.max_tokens_spin.value(),
            "top_p": self.top_p_spin.value(),
            "enable_python_tool": self.enable_python_tool.isChecked()
        }
