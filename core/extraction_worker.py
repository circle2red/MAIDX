"""
Extraction Worker - Background thread for processing files
"""
from PySide6.QtCore import QThread, Signal
from typing import List, Dict, Any
import json
import os
from core.llm_client import LLMClient
from core.file_parsers import parse_file


class ExtractionWorker(QThread):
    """Worker thread for extracting data from files"""

    progress = Signal(int, int)  # current, total
    log = Signal(str)
    finished = Signal()
    error = Signal(str)

    def __init__(self, files: List[str], model_config: Dict[str, Any],
                 schema_config: Dict[str, Any], output_file: str,
                 multiple_per_file: bool = False):
        super().__init__()
        self.files = files
        self.model_config = model_config
        self.schema_config = schema_config
        self.output_file = output_file
        self.multiple_per_file = multiple_per_file
        self.should_stop = False

    def stop(self):
        """Stop the extraction process"""
        self.should_stop = True

    def run(self):
        """Run the extraction process"""
        try:
            # Initialize LLM client
            self.log.emit("Initializing LLM client...")
            llm_client = LLMClient(self.model_config)

            # Prepare schema information
            schema_info = self.prepare_schema_info()

            # Initialize output directory for JSON files
            self.json_output_dir = self.output_file
            if not os.path.exists(self.json_output_dir):
                os.makedirs(self.json_output_dir)
            self.log.emit(f"JSON output directory: {self.json_output_dir}")

            # Process each file
            total = len(self.files)
            for i, file_path in enumerate(self.files):
                if self.should_stop:
                    self.log.emit("Extraction stopped by user.")
                    return

                self.progress.emit(i + 1, total)
                self.log.emit(f"Processing: {os.path.basename(file_path)}")

                try:
                    # Parse file content
                    content = parse_file(file_path)
                    if content is None:
                        self.log.emit(f"Skipping unsupported file: {os.path.basename(file_path)}")
                        continue

                    if content.startswith("[Error"):
                        self.log.emit(f"Error reading file: {content}")
                        continue

                    # Extract data using LLM
                    extracted = self.extract_from_content(
                        llm_client, content, schema_info, file_path
                    )

                    # Save extracted data to JSON files
                    if extracted:
                        self.save_extracted_data_json(extracted, file_path, i)
                        self.log.emit(f"Extracted {len(extracted) if isinstance(extracted, list) else 1} record(s)")

                except Exception as e:
                    self.log.emit(f"Error processing {os.path.basename(file_path)}: {str(e)}")
                    continue

            self.log.emit("Extraction completed successfully!")
            self.finished.emit()

        except Exception as e:
            self.error.emit(str(e))

    def prepare_schema_info(self) -> str:
        """Prepare schema information for the LLM prompt"""
        # Use the full JSON schema if available
        raw_schema = self.schema_config.get('raw_schema', '')
        if raw_schema:
            schema_info = f"Extract data according to the following JSON Schema:\n\n{raw_schema}"
        else:
            fields = self.schema_config['fields']
            field_descriptions = []
            for field in fields:
                desc = f"- {field['name']} ({field['type']})"
                if field['description']:
                    desc += f": {field['description']}"
                field_descriptions.append(desc)

            schema_info = "Extract data as JSON with fields:\n"
            schema_info += "\n".join(field_descriptions)

        return schema_info

    def extract_from_content(self, llm_client: LLMClient, content: str,
                           schema_info: str, file_path: str) -> Any:
        """Extract structured data from content using LLM"""

        # Build the extraction prompt
        if self.multiple_per_file:
            quantity_instruction = "Extract ALL matching records from this content. Return an array of records if there are multiple."
        else:
            quantity_instruction = "Extract ONE record from this content."

        format_instruction = """
Return the result as valid JSON that conforms to the provided JSON Schema.
- For nested objects, include all required nested fields
- For arrays, include all array items with their proper structure
- Ensure all data types match the schema specifications
- IMPORTANT: If you need to perform calculations or conversions, use the execute_python tool.

Return ONLY the JSON data that matches the schema. Do not include the schema itself in your response.
"""

        system_prompt = f"""You are a data extraction assistant. Your task is to extract structured data from documents according to a given schema.

Schema:
{schema_info}

Instructions:
{quantity_instruction}
{format_instruction}

Return ONLY valid JSON. Do not include any explanatory text outside the JSON."""

        user_prompt = f"""Extract data from the following content:

File: {os.path.basename(file_path)}

Content:
{content[:10000]}  # Limit content length
"""

        # Call LLM with tool support
        response = llm_client.call_with_tools(system_prompt, user_prompt)

        # Parse the response
        response_text = response['content'].strip()

        # Extract JSON from response
        extracted_data = self.parse_llm_response(response_text)

        return extracted_data

    def parse_llm_response(self, response_text: str) -> Any:
        """Parse the LLM response to extract JSON data"""
        # Try to find JSON in the response
        response_text = response_text.strip()

        # Remove Markdown code blocks if present
        if response_text.startswith('```'):
            lines = response_text.split('\n')
            # Remove first and last lines
            response_text = '\n'.join(lines[1:-1])

        if response_text.startswith('```json'):
            response_text = response_text[7:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]

        response_text = response_text.strip()

        try:
            data = json.loads(response_text)
            return data
        except json.JSONDecodeError as e:
            self.log.emit(f"Failed to parse JSON response: {str(e)}")
            self.log.emit(f"Response was: {response_text[:200]}")
            return None

    def save_extracted_data_json(self, data: Any, source_file_path: str, file_index: int):
        """Save extracted data to separate JSON file(s)"""
        # Get base filename without extension
        base_name = os.path.splitext(os.path.basename(source_file_path))[0]

        # Normalize data to list
        if not isinstance(data, list):
            data_list = [data]
        else:
            data_list = data

        # Save each record to a separate file
        for record_index, record in enumerate(data_list):
            if len(data_list) > 1:
                # Multiple records - add record number
                output_filename = f"{base_name}_record_{record_index + 1}.json"
            else:
                # Single record
                output_filename = f"{base_name}_extracted.json"

            output_path = os.path.join(self.json_output_dir, output_filename)

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(record, f, indent=2, ensure_ascii=False)

            self.log.emit(f"Saved: {output_filename}")
