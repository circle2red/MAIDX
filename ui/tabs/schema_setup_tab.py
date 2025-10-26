"""
Schema Setup Tab - Define data extraction schema
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                               QLabel, QComboBox, QLineEdit, QPushButton,
                               QTextEdit, QTreeWidget, QTreeWidgetItem,
                               QFormLayout, QMessageBox, QHeaderView)
from PySide6.QtCore import Signal, Qt
import json


class SchemaSetupTab(QWidget):
    """Tab for defining the extraction schema"""

    schema_changed = Signal()

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # JSON Schema Title
        title_layout = QHBoxLayout()
        title_layout.addWidget(QLabel("Schema Title:"))
        self.json_title_input = QLineEdit()
        self.json_title_input.setPlaceholderText("e.g., Invoice Details")
        title_layout.addWidget(self.json_title_input)
        layout.addLayout(title_layout)

        # Field Definition Group
        fields_group = QGroupBox("Field Definitions")
        fields_layout = QVBoxLayout()

        # Tree for fields (supports hierarchy)
        self.fields_tree = QTreeWidget()
        self.fields_tree.setColumnCount(3)
        self.fields_tree.setHeaderLabels(["Field Name", "Type", "Required", "Description"])
        # self.fields_tree.header().setSectionResizeMode(0, QHeaderView.Interactive)
        # self.fields_tree.header().setSectionResizeMode(1, QHeaderView.Interactive)
        # self.fields_tree.header().setSectionResizeMode(2, QHeaderView.Stretch)
        self.fields_tree.setColumnWidth(0, 200)
        self.fields_tree.setColumnWidth(1, 50)
        self.fields_tree.setColumnWidth(2, 60)

        self.fields_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        fields_layout.addWidget(self.fields_tree)


        # First row - field name and type
        row1 = QHBoxLayout()
        self.field_name_input = QLineEdit()
        self.field_name_input.setPlaceholderText("Field name")
        row1.addWidget(QLabel("Name:"))
        row1.addWidget(self.field_name_input)

        self.field_type_combo = QComboBox()
        self.field_type_combo.addItems(["string", "number", "integer", "boolean", "array", "object"])
        # self.field_type_combo.currentTextChanged.connect(self.on_field_type_changed)
        row1.addWidget(QLabel("Type:"))
        row1.addWidget(self.field_type_combo)


        self.required_combo = QComboBox()
        self.required_combo.addItems(["True", "False"])
        # self.required_combo.currentTextChanged.connect(self.on_field_type_changed)
        row1.addWidget(QLabel("Required:"))
        row1.addWidget(self.required_combo)

        fields_layout.addLayout(row1)

        # Second row - description
        row2 = QHBoxLayout()
        self.field_desc_input = QLineEdit()
        self.field_desc_input.setPlaceholderText("Description/hint for LLM")
        row2.addWidget(QLabel("Description:"))
        row2.addWidget(self.field_desc_input)
        fields_layout.addLayout(row2)

        # Third row - buttons
        row3 = QHBoxLayout()
        self.add_field_btn = QPushButton("Add Root Field")
        self.add_field_btn.clicked.connect(lambda: self.add_field(None))
        row3.addWidget(self.add_field_btn)

        self.add_child_btn = QPushButton("Add Child to Selected")
        self.add_child_btn.clicked.connect(self.add_child_field)
        row3.addWidget(self.add_child_btn)

        self.delete_field_btn = QPushButton("Delete Selected")
        self.delete_field_btn.clicked.connect(self.delete_selected_field)
        row3.addWidget(self.delete_field_btn)

        row3.addStretch()
        fields_layout.addLayout(row3)

        fields_group.setLayout(fields_layout)
        layout.addWidget(fields_group)

        # Raw Schema Input/Output
        raw_group = QGroupBox("Full Schema Definition")
        raw_layout = QVBoxLayout()

        info_label = QLabel(
            "For complex schemas with nested objects/arrays, edit the JSON Schema directly below.\n"
            "The schema follows JSON Schema Draft 7 specification."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666; font-style: italic;")
        raw_layout.addWidget(info_label)

        self.schema_text = QTextEdit()
        self.schema_text.setPlaceholderText(self.get_placeholder_text())
        self.schema_text.textChanged.connect(self.on_raw_schema_changed)
        raw_layout.addWidget(self.schema_text)

        # Buttons for raw schema
        btn_layout = QHBoxLayout()

        self.load_example_btn = QPushButton("Load Example")
        self.load_example_btn.clicked.connect(self.load_example_schema)
        btn_layout.addWidget(self.load_example_btn)

        self.load_json_btn = QPushButton("Load Current JSON To Editor")
        self.load_json_btn.clicked.connect(self.load_json)
        btn_layout.addWidget(self.load_json_btn)

        self.generate_btn = QPushButton("Load Editor to JSON")
        self.generate_btn.clicked.connect(self.generate_schema)
        btn_layout.addWidget(self.generate_btn)

        self.validate_btn = QPushButton("Validate JSON Schema")
        self.validate_btn.clicked.connect(self.validate_schema)
        btn_layout.addWidget(self.validate_btn)

        btn_layout.addStretch()

        raw_layout.addLayout(btn_layout)
        raw_group.setLayout(raw_layout)
        layout.addWidget(raw_group)

        layout.addStretch()

    def get_placeholder_text(self):
        """Get placeholder text for schema editor"""
        return """{
  "title": "Data Schema",
  "type": "object",
  "properties": {
    "field1": {
      "type": "string",
      "description": "Description here"
    },
    "nested_object": {
      "type": "object",
      "properties": {
        "subfield": {"type": "number"}
      }
    },
    "array_field": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "item_field": {"type": "string"}
        }
      }
    }
  }
}"""


    def load_json(self):
        try:
            schema = json.loads(self.schema_text.toPlainText())
            self.json_title_input.setText(schema.get("title", "Data Schema").strip())

            # Also populate the tree widget with the example
            self.fields_tree.clear()
            self.populate_tree_from_schema(schema.get("properties", {}), schema.get("required", []))
        except Exception as e:
            QMessageBox.warning(self, "Error Parsing JSON", f"Error when parsing JSON: {e}")

    def load_example_schema(self):
        """Load an example invoice schema"""
        example = {
            "title": "Invoice Details",
            "description": "Schema to hold structured data extracted from an invoice.",
            "type": "object",
            "properties": {
                "invoice_id": {
                    "type": "string",
                    "description": "The unique identifier for the invoice, often prefixed (e.g., 'IN-')."
                },
                "issue_date": {
                    "type": "string",
                    "format": "date",
                    "description": "The date the invoice was issued, in YYYY-MM-DD format."
                },
                "customer_name": {
                    "type": "string",
                    "description": "The name of the company or individual being billed."
                },
                "line_items": {
                    "type": "array",
                    "description": "A list of all items or services being billed on the invoice.",
                    "items": {
                        "type": "object",
                        "description": "A single billable item or service.",
                        "properties": {
                            "item_description": {
                                "type": "string",
                                "description": "The name or description of the product or service."
                            },
                            "quantity": {
                                "type": "integer",
                                "description": "The number of units of the item."
                            },
                            "unit_price": {
                                "type": "number",
                                "description": "The cost for a single unit of the item."
                            }
                        },
                        "required": ["item_description", "quantity", "unit_price"]
                    }
                },
                "total_amount": {
                    "type": "number",
                    "description": "The final total amount due for the invoice."
                }
            },
            "required": [
                "invoice_id",
                "issue_date",
                "customer_name",
                "line_items",
                "total_amount"
            ]
        }

        self.schema_text.setPlainText(json.dumps(example, indent=2))
        self.load_json()

    def populate_tree_from_schema(self, properties, required, parent_item=None):
        """Populate tree widget from JSON Schema properties"""
        for prop_name, prop_def in properties.items():
            prop_type = prop_def.get("type", "string")
            prop_desc = prop_def.get("description", "")

            # Create tree item
            item = QTreeWidgetItem()
            item.setText(0, prop_name)
            item.setText(1, prop_type)
            if prop_name in required:
                item.setText(2, "True")
            else:
                item.setText(2, "False")
            item.setText(3, prop_desc)

            # Store data
            item.setData(0, Qt.UserRole, {
                "name": prop_name,
                "type": prop_type,
                "description": prop_desc
            })

            if parent_item is None:
                self.fields_tree.addTopLevelItem(item)
            else:
                parent_item.addChild(item)

            # Handle nested properties
            if prop_type == "object" and "properties" in prop_def:
                self.populate_tree_from_schema(prop_def["properties"], prop_def["required"], item)
                item.setExpanded(True)
            elif prop_type == "array" and "items" in prop_def:
                items_def = prop_def["items"]
                if items_def.get("type") == "object" and "properties" in items_def:
                    # Array of objects
                    self.populate_tree_from_schema(items_def["properties"], items_def["required"], item)
                    item.setExpanded(True)

    def validate_schema(self):
        """Validate the schema"""
        schema_text = self.schema_text.toPlainText().strip()

        if not schema_text:
            QMessageBox.warning(self, "Empty Schema", "Please enter a schema first.")
            return

        try:
            self.validate_json_schema(schema_text)
            QMessageBox.information(self, "Valid", "Schema is valid!")
        except Exception as e:
            QMessageBox.warning(self, "Invalid Schema", f"Schema validation failed:\n{str(e)}")

    def validate_json_schema(self, schema_text: str):
        """
        Validate JSON syntax and schema structure, disallowing duplicate keys.
        """
        def _reject_duplicate_keys(pairs):
            """A hook for json.loads to fail on duplicate keys."""
            keys = set()
            result = {}
            for key, value in pairs:
                if key in keys:
                    raise ValueError(f"Duplicate key found in JSON object: '{key}'")
                keys.add(key)
                result[key] = value
            return result

        try:
            # Use the hook to parse the JSON. This validates syntax AND checks for duplicates.
            schema = json.loads(schema_text, object_pairs_hook=_reject_duplicate_keys)
        except json.JSONDecodeError as e:
            # Catch badly formed JSON
            raise ValueError(f"Invalid JSON syntax: {e}") from e
        except ValueError as e:
            # Catch duplicate keys or other ValueErrors from the hook
            raise e

        # Additional JSON Schema validation (your original checks)
        if "properties" in schema and not isinstance(schema.get("properties"), dict):
            raise ValueError("'properties' must be an object")

        # Check for common JSON Schema fields
        valid_types = {"object", "array", "string", "number", "integer", "boolean", "null"}
        if schema.get("type") and schema["type"] not in valid_types:
            raise ValueError(f"Invalid type: {schema['type']}. Must be one of {valid_types}")


    def add_field(self, parent_item):
        """Add a field to the schema tree"""
        name = self.field_name_input.text().strip()
        field_type = self.field_type_combo.currentText()
        required = self.required_combo.currentText()
        description = self.field_desc_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Invalid Input", "Field name cannot be empty.")
            return

        # Create tree item
        item = QTreeWidgetItem()
        item.setText(0, name)
        item.setText(1, field_type)
        item.setText(2, required)
        item.setText(3, description)

        # Store additional data
        # item.setData(0, Qt.UserRole, {
        #     "name": name,
        #     "type": field_type,
        #     "description": description
        # })

        if parent_item is None:
            # Add as root item
            for i in range(self.fields_tree.topLevelItemCount()):
                hist_item = self.fields_tree.topLevelItem(i)
                field_name = hist_item.text(0)
                if name == field_name:
                    QMessageBox.warning(self, "Invalid Input", f"{name} already exists in root!")
                    return
            self.fields_tree.addTopLevelItem(item)
        else:
            # Add as child
            for i in range(parent_item.childCount()):
                hist_item = parent_item.child(i)
                field_name = hist_item.text(0)
                if name == field_name:
                    QMessageBox.warning(self, "Invalid Input", f"{name} already exists in  {parent_item.text(0)}!")
                    return
            parent_item.addChild(item)
            parent_item.setExpanded(True)

        # Clear inputs
        self.field_name_input.clear()
        self.field_desc_input.clear()

        self.schema_changed.emit()

    def add_child_field(self):
        """Add a child field to the selected item"""
        selected = self.fields_tree.selectedItems()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select a parent field (must be object or array type).")
            return

        parent_item = selected[0]
        parent_type = parent_item.text(1)

        # Validate parent type
        if parent_type not in ["object", "array"]:
            QMessageBox.warning(self, "Invalid Parent",
                              "Parent field must be of type 'object' or 'array' to have children.")
            return

        self.add_field(parent_item)

    def delete_selected_field(self):
        """Delete the selected field from the tree"""
        selected = self.fields_tree.selectedItems()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select a field to delete.")
            return

        item = selected[0]
        parent = item.parent()

        if parent is None:
            # Top level item
            index = self.fields_tree.indexOfTopLevelItem(item)
            self.fields_tree.takeTopLevelItem(index)
        else:
            # Child item
            parent.removeChild(item)

        self.schema_changed.emit()

    def tree_to_fields_list(self):
        """Convert tree structure to flat fields list (for backward compatibility)"""
        fields = []

        def traverse(item, depth=0):
            data = item.data(0, Qt.UserRole)
            if data:
                fields.append(data)

            for i in range(item.childCount()):
                traverse(item.child(i), depth + 1)

        for i in range(self.fields_tree.topLevelItemCount()):
            traverse(self.fields_tree.topLevelItem(i))

        return fields

    def tree_item_to_schema(self, item):
        """Convert a tree item to JSON Schema property definition"""
        name = item.text(0)
        field_type = item.text(1)
        required = item.text(2)
        description = item.text(3)

        property_def = {"type": field_type}

        if description:
            property_def["description"] = description

        # Handle object type with children
        if field_type == "object" and item.childCount() > 0:
            property_def["properties"] = {}
            property_def["required"] = []

            for i in range(item.childCount()):
                child = item.child(i)
                child_name = child.text(0)
                child_def = self.tree_item_to_schema(child)
                property_def["properties"][child_name] = child_def
                if child.text(2) != "False":
                    property_def["required"].append(child_name)

        # Handle array type with children
        elif field_type == "array" and item.childCount() > 0:
            # For arrays, the first child defines the item schema
            if item.childCount() == 1:
                first_child = item.child(0)
                property_def["items"] = self.tree_item_to_schema(first_child)
                property_def["description"] = description or f"Array of {first_child.text(0)} items"
            else:
                # Multiple children - treat as object schema for array items
                property_def["items"] = {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
                for i in range(item.childCount()):
                    child = item.child(i)
                    child_name = child.text(0)
                    child_def = self.tree_item_to_schema(child)
                    property_def["items"]["properties"][child_name] = child_def
                    if child.text(2) != "False":
                        property_def["items"]["required"].append(child_name)

        return property_def

    def generate_schema(self):
        """Generate schema text from fields tree"""
        if self.fields_tree.topLevelItemCount() == 0:
            QMessageBox.warning(self, "No Fields", "Please add fields first.")
            return

        schema = {
            "title": self.json_title_input.text().strip() or "Data Schema",
            "type": "object",
            "properties": {},
            "required": []
        }

        # Process each top-level item
        for i in range(self.fields_tree.topLevelItemCount()):
            item = self.fields_tree.topLevelItem(i)
            field_name = item.text(0)
            property_def = self.tree_item_to_schema(item)

            schema["properties"][field_name] = property_def
            if item.text(2) != "False":
                schema["required"].append(field_name)

        schema_text = json.dumps(schema, indent=2, ensure_ascii=False)

        self.schema_text.setPlainText(schema_text)
        self.schema_changed.emit()

    def on_raw_schema_changed(self):
        """Handle manual editing of raw schema"""
        self.schema_changed.emit()

    def get_schema_config(self):
        """Get the schema configuration"""
        raw_schema = self.schema_text.toPlainText().strip()

        # Get fields from tree structure
        fields = self.tree_to_fields_list()

        config = {
            "type": "JSON Schema",
            "json_title": self.json_title_input.text().strip() or "Data Schema",
            "fields": fields,
            "raw_schema": raw_schema
        }

        # Parse and include the actual JSON schema object
        if raw_schema:
            try:
                config["json_schema"] = json.loads(raw_schema)
            except:
                config["json_schema"] = None

        return config
