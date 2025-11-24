"""
Extraction Worker - Background thread for processing files
"""
from PySide6.QtCore import QThread, Signal
from typing import List, Dict, Any, Optional
import json
import os
import re

import core.llm_tools.schema_validation_tool
from core.llm_tools.tools_manager import ToolsManager
from core.llm_client import LLMClient, parse_code_fences
from core.file_manager import FileManager
from core.llm_prompt import system_prompt, user_prompt
from core.llm_tools.schema_validation_tool import validate_against_schema

SCHEMA_TOOL_NAME = core.llm_tools.schema_validation_tool.TOOL_NAME

class ExtractionThread(QThread):
    """Worker thread for extracting data from files"""

    progress = Signal(int, int)  # current, total
    log = Signal(str)
    ext_finished = Signal()  # Extraction finished signal, must not be named "finished" (conflict with QThread builtin finished signal)
    error = Signal(str)

    def __init__(self, model_config: Dict[str, Any],
                 schema_config: Dict[str, Any], method_config: Dict[str, Any],
                 extraction_config: Dict[str, Any]):
        super().__init__()
        self.should_stop = False
        self.model_config = model_config
        self.schema_config = schema_config
        self.method_config = method_config
        self.extraction_config = extraction_config
        self.file_manager = None
        self.llm_client = None
        self.tools_manager = None

    def stop(self):
        """Stop the extraction process"""
        self.should_stop = True

    def run(self):
        """Run the extraction process"""
        try:
            self.log.emit("Parsing Files...")
            self.file_manager = FileManager(
                file_list=self.extraction_config['files'],
                output_path=self.extraction_config['output_folder'],
                pdf_parse_mode=self.method_config['pdf_mode'],
                use_segment=self.method_config['use_segmentation'],
                max_seg_text_len=self.method_config['max_text_length'],
                max_seg_page_cnt=self.method_config['max_pages_count'],
                seg_overlap=self.method_config['overlapping_length'],
            )

            self.log.emit("Setting up LLM tools...")
            # Pass schema for validation if enabled

            schema_dict = self.schema_config['json_schema']

            self.tools_manager = ToolsManager(
                python_limit=self.method_config['max_python_call'],
                web_fetch_limit=self.method_config['max_web_fetch_call'],
                schema=schema_dict,
                schema_validation_limit=self.method_config['max_validation_retries'],
            )

            self.log.emit("Initializing LLM client...")
            self.llm_client = LLMClient(
                endpoint=self.model_config['endpoint'],
                model_name=self.model_config['model'],
                headers=self.model_config['headers'],
                tools_manager=self.tools_manager,
                temperature=self.model_config['temperature'],
                max_tokens=self.model_config['max_tokens'],
                top_p=self.model_config['top_p'],
                timeout=self.model_config['timeout'],
            )

            # Prepare schema information
            schema_desc = self.prepare_schema_info()

            # Initialize output directory for JSON files
            self.log.emit(f"JSON output directory: {self.file_manager.output_path}")

            # Process each file
            total = self.file_manager.get_file_count()
            for i, file_path in enumerate(self.file_manager.get_file_names()):
                if self.should_stop:
                    self.log.emit("Extraction stopped by user.")
                    return

                self.log.emit(f"Processing: {os.path.basename(file_path)}")

                self.llm_client.clear_history()  # clear tool use
                last_resp = ""
                segments = self.file_manager.get_segments(file_path)

                try:
                    for segment_id, segment_content in enumerate(segments):
                        self.llm_client.messages = []     # clear messages but not tool use
                        if self.method_config['use_segmentation']:
                            segment_status = (segment_id+1, len(segments))
                        else:
                            segment_status = None
                        self.llm_client.add_text_message(
                            "system",
                            system_prompt(json_schema_description=schema_desc,
                                          tools_desc=self.method_config['tool_prompt'],
                                          multiple_per_file=self.method_config['multi_obj'],
                                          segment_status=segment_status)
                        )
                        self.llm_client.add_text_message(
                            "user",
                            user_prompt(content=segment_content['text'],
                                        prev_history=last_resp,
                                        segment_status=segment_status,
                                        file_name=self.file_manager.strip_file_name(file_path))
                        )
                        for img in segment_content['img']:
                            self.llm_client.add_image_message("user",
                                                              img_b64=img)

                        pass_schema_check = False

                        while not pass_schema_check:
                            pass_schema_check = True
                            resp = self.llm_client.send_llm_request()
                            last_resp = ""
                            result = []
                            objs = parse_code_fences(resp)
                            for obj in objs:
                                if '%missing%' in obj:
                                    last_resp += f"```\n{obj}\n```\n"
                                else:
                                    if self.schema_config['force_retry_on_validation_failure']:
                                        validation_result = validate_against_schema(schema=schema_dict, data_str=obj)
                                        if validation_result['valid']:
                                            result.append(obj)
                                        else:
                                            errors = '\n'.join(i['message'] for i in validation_result['errors'])
                                            self.llm_client.add_text_message("user", f"Schema check failed for obj: \n```\n{obj}\n```\n, "
                                                                                     f"Please fix the following errors: {errors}")
                                            pass_schema_check = False
                                    else:
                                        result.append(obj)

                        if self.extraction_config['log_raw']:
                            self.file_manager.append_log_for_file(
                                filename=file_path,
                                log=self.llm_client.messages,
                            )
                        self.file_manager.append_result_for_file(
                            filename=file_path,
                            result=result,
                        )
                        self.log.emit(f"  > Extracted Parts {segment_id + 1} / {len(segments)}")

                    self.log.emit(f"  > File Finished.")
                except Exception as e:
                    self.log.emit(f"Error processing {os.path.basename(file_path)}: {str(e)}")
                    continue
                self.progress.emit(i + 1, total)

            self.ext_finished.emit()
        except Exception as e:
            self.error.emit(str(e))

    def prepare_schema_info(self) -> str:
        """Prepare schema information for the LLM prompt"""
        # Use the full JSON schema if available
        raw_schema = self.schema_config.get('raw_schema', '{}')
        schema_info = f"Extract data according to the following JSON Schema:\n\n{raw_schema}"
        return schema_info

