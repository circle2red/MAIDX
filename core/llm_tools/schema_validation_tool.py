"""
Schema validation tool factory to create validation tools with predefined schemas
"""
import json
import jsonschema
from jsonschema import Draft7Validator, exceptions
import copy

TOOL_NAME = "schema_validation"


def validate_against_schema(schema, data_str):
    """
    Validate a JSON object against a JSON schema.

    Args:
        schema (dict): JSON schema object
        data_str (str): JSON data to validate

    Returns:
        dict: Validation result with keys:
            - valid (bool): True if validation passed, False otherwise
            - errors (list): List of validation errors (empty if valid)
    """
    try:
        # Parse data
        data = json.loads(data_str)

        # Create validator
        validator = Draft7Validator(schema)

        # Collect validation errors
        errors = list(validator.iter_errors(data))

        if errors:
            error_details = []
            for error in errors:
                # Format the error path for better readability
                path = ".".join(str(p) for p in error.path) if error.path else "(root)"
                error_details.append({
                    "path": path,
                    "message": error.message,
                    "schema_path": ".".join(str(p) for p in error.schema_path)
                })

            return {
                "valid": False,
                "errors": error_details
            }

        return {
            "valid": True,
            "errors": []
        }

    except json.JSONDecodeError as e:
        return {
            "valid": False,
            "errors": [{
                "path": "(parsing)",
                "message": f"Invalid JSON: {str(e)}",
                "schema_path": ""
            }]
        }
    except Exception as e:
        return {
            "valid": False,
            "errors": [{
                "path": "(unknown)",
                "message": f"Validation error: {str(e)}",
                "schema_path": ""
            }]
        }


class SchemaValidationToolFactory:
    """Factory to create schema validation tools with predefined schemas"""

    @staticmethod
    def create_tool(schema):
        """
        Create a schema validation tool with a predefined schema.

        Args:
            schema (dict or str): The JSON schema to validate against
            tool_name (str): Optional custom name for the tool

        Returns:
            tuple: (tool_description, validation_function)
        """
        # Parse schema if it's a string
        if isinstance(schema, str):
            try:
                parsed_schema = json.loads(schema)
            except json.JSONDecodeError:
                raise ValueError("Invalid JSON schema provided")
        else:
            parsed_schema = schema

        # Create tool description
        schema_title = parsed_schema.get("title", "Data")

        tool_description = {
            "type": "function",
            "function": {
                "name": TOOL_NAME,
                "description": f"Validate JSON data against the predefined schema for '{schema_title}'.\n"
                               "This tool ensures that extracted data conforms to the required structure.\n\n"
                               "Only provide the JSON data to validate. The schema is already defined in the system.\n"
                               "You'll receive validation results with any errors found.\n\n"
                               "Common validation issues include:\n"
                               "- Missing required fields\n"
                               "- Incorrect data types (e.g., string instead of number)\n"
                               "- Invalid formats for dates, emails, etc.\n",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "data": {
                            "type": "string",
                            "description": "The JSON data to validate (as a string)"
                        }
                    },
                    "required": ["data"]
                }
            }
        }

        # Create validation function
        def validation_function(data):
            # Perform validation
            result = validate_against_schema(parsed_schema, data)

            # Format the response
            if result["valid"]:
                return "Validation succeeded! The data conforms to the schema."
            else:
                error_message = "Validation failed! The following errors were found:\n\n"
                for i, error in enumerate(result["errors"], 1):
                    error_message += f"{i}. At path '{error['path']}': {error['message']}\n"

                return error_message

        return tool_description, validation_function


if __name__ == '__main__':
    print("Test: schema is nutrition")
    schema_test = json.loads(
        '{"title": "Food Nutrition", "type": "object", "properties": {"net_weight": {"type": "string", "description": "The net weight of the entire package as labeled"}, "nutrition_on_label": {"type": "object", "description": "Nutrition table on the product", "properties": {"energy": {"type": "number", "description": "Energy content in kilocalories (kcal)."}, "protein": {"type": "number", "description": "Protein content in grams (g)."}, "unit": {"type": "string", "description": "The unit in table (e.g. 100g)"}}, "required": ["energy", "unit"]}, "nutrition_per_package": {"type": "object", "description": "Total nutrient content for the entire package, based on net weight.", "properties": {"energy": {"type": "number", "description": "Total energy in the package in kilocalories (kcal)."}, "protein": {"type": "number", "description": "Total protein in the package in grams (g)."}}, "required": ["energy"]}, "barcode": {"type": "number", "description": "The barcode of the food"}}, "required": ["net_weight", "nutrition_on_label", "nutrition_per_package", "barcode"]}')
    _, tool = SchemaValidationToolFactory.create_tool(schema=schema_test)
    print(tool(
        '{"net_weight": "350 mL", "nutrition_on_label": {"energy": 21, "unit": "100 mL"}, "nutrition_per_package": {"energy": 73.5}, "barcode": 8859015700168}'))
    print(tool(
        '{"net_weight": "350 mL", "nutrition_on_label": {"energy": "cat", "unit": "100 mL"}, "nutrition_per_package": {"energy": 73.5}, "barcode": 8859015700168}'))
