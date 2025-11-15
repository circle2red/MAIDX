from typing import List


def system_prompt(json_schema: str, tools_desc: str,
                  multiple_per_file=False, segment_status=None):
    """
    Format a system prompt for LLM.
    multiple_per_file: Extract multiple files per file or only one
    segment_status: If segmentation is enabled, (a, b) indicates segment a of b; otherwise set to None.
    """
    if not tools_desc.endswith("\n\n"):
        tools_desc += "\n\n"
    segment_instruction = ""
    if segment_status and segment_status[1] != 1:
        if multiple_per_file:
            quantity_instruction = "Extract ALL matching records from the provided content. " \
                                   "Return multiple code fences if there are multiple."
        else:
            quantity_instruction = "Extract ONE record from all the content, wrapped by a code fence."

        if segment_status[0] != segment_status[1]:
            segment_instruction = f"\n\n" \
                                  f"IMPORTANT: The provided content is a segment of a whole document. " \
                                  f"Please make best effort to extract the content. " \
                                  f"If you can identify one incomplete object, please keep it and use %missing% " \
                                  f"to mark the missing attributes in your output. " \
                                  f"If you can fill in the missing part of previous objects, please" \
                                  f" delete the %missing% mark and complete it in full."
        else:
            segment_instruction = f"\n\n" \
                                  f"IMPORTANT: The provided content is a segment of a whole document, " \
                                  f"and this is the final segment of the data. " \
                                  f"Please make best effort to extract the content. " \
                                  f"Please fill in all the %missing% attributes."
    else:
        if multiple_per_file:
            quantity_instruction = "Extract ALL matching records from this content. " \
                                   "Return multiple code fences if there are multiple."
        else:
            quantity_instruction = "Extract ONE record from this content, wrapped by a code fence."

    return f"You are a data extraction assistant. " \
           f"Your task is to extract structured data from documents according to a given schema.\n\n" \
           f"Schema: Extract data according to the following JSON Schema: {json_schema}\n\n" \
           f"Instructions: {quantity_instruction}\n " \
           f"Return the result as valid JSON that conforms to the provided JSON Schema.\n" \
           f" - For nested objects, include all required nested fields\n" \
           f" - For arrays, include all array items with their proper structure\n" \
           f" - Ensure all data types match the schema specifications\n" \
           f" - If no data can be extracted, return an empty code fence, do not make up data.\n\n" \
           f"{tools_desc}" \
           f"IMPORTANT: Return ONLY the JSON data that matches the schema. " \
           f"Do not include the schema itself in your response. " \
           f"Return ONLY valid JSON wrapped by code fences ```. " \
           f"Do not include any explanatory text outside the JSON." \
           f"{segment_instruction}"


def user_prompt(content, prev_history=None, segment_status=None, file_name=""):
    prompt = ""
    if segment_status and segment_status[1] != 1:
        prompt += f"File: {file_name} (Segment {segment_status[0]} of {segment_status[1]})\n\n"
    else:
        prompt += f"File: {file_name}\n\n"
    if prev_history:
        prompt += f"Previous Partial Objects: {prev_history}\n\n"
    if content:
        prompt += f"Content:\n {content}"
    return prompt

