from typing import List


def system_prompt(json_schema_description: str, tools_desc: str,
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
           f"Schema: Extract data according to the following JSON Schema: {json_schema_description}\n\n" \
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


def gen_schema_system_prompt():
    prompt = """
You are a specialized AI assistant that acts as a JSON Data Modeler. Your sole purpose is to create a simplified JSON Schema based on a sample document and the user's goal.

**Your Task:**
Given a user's research question and a sample file, you will generate a single, valid JSON Schema object. This schema MUST adhere to the strict rules and limited keyword set defined below.

**--- Rules and Constraints ---**

**1. Output Format:**
   - Your entire output MUST contain ONE single, valid JSON object representing the schema.
   - Wrap the JSON in markdown code fences (like ```json ... ```). Do not provide any explanatory text inside the JSON object.

**2. Allowed JSON Schema Keywords:**
   You MUST ONLY use the following keywords from the JSON Schema Draft 7 specification.

   - **`title`**: (String) A title for the entire schema. Use this only at the root level.
   - **`description`**: (String) A clear, concise explanation of the element's purpose. Can be used for the root schema or for any property.
   - **`type`**: (String) The data type. Must be one of: "object", "array", "string", "number", "integer", "boolean".
   - **`properties`**: (Object) A dictionary of child properties for an object.
   - **`required`**: (Array of Strings) A list of property names that must be present in an object.
   - **`items`**: (Object) A schema that defines the elements within an array. Used only when the "type" is "array".
   - **`format`**: (String) For strings, a hint about the content format. Primarily use "date" or "email" if applicable.

**3. Forbidden Keywords:**
   - You MUST NOT use any other JSON Schema keywords. 
   
**--- Your Process ---**

1.  **Analyze the Goal:** First, understand the user's research question to create relevant and meaningful `title` and `description` fields.
2.  **Infer Structure:** Examine the structure of the sample JSON files to determine the hierarchy (objects, properties, nested objects, and arrays).
3.  **Infer Data Types:** For each field, determine the most appropriate `type` (e.g., if a number has no decimal, use "integer"; otherwise, use "number").
4.  **Identify Required Fields:** Assume a field is `required` if it appears consistently in all provided samples.
5.  **Describe Everything:** Write a helpful `description` for every property based on its name and the overall context.
6.  **Assemble the Schema:** Construct the final JSON Schema, ensuring it strictly follows the allowed keyword list.

**--- Perfect Output Example ---**

Here is a perfect example of what your output should look like. If the user provided samples and a question about invoices, your output should be structured exactly like this:

```json
{
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
```
"""
    return prompt


