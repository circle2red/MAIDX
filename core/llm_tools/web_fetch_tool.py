import json.decoder

import httpx

tool_desc = {
    "type": "function",
    "function": {
        "name": "web_fetch",
        "description": "Use this to fetch the Internet resources, preferably APIs. \n"
                       "You should specify the URL, the method (GET/POST), "
                       "and optionally the body of POST request (JSON). "
                       "You will be returned with the result (first 10KB if too large). \n"
                       "Suggestion: Use this on known APIs instead of requesting HTMLs as they are usually too large.",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "Webpage URL, must start with http:// or https://",
                },
                "method": {
                    "type": "string",
                    "description": "Method of sending a request, must be GET or POST"
                },
                "body": {
                    "type": "string",
                    "description": "Optional request body in JSON format"
                },
            },
            "required": ["url", "method"]
        },
    }
}


def web_fetch(url: str, method: str, body: str = None) -> str:
    """
    Fetch the internet
    """

    method = method.strip().upper()
    if method == "GET":
        request = httpx.get(url)
        return f"Status Code: {request.status_code}\nResponse: {request.text}"

    if method == "POST":
        try:
            request = httpx.post(url, json=body)
            return f"Status Code: {request.status_code}\nResponse: {request.text}"
        except json.decoder.JSONDecodeError as e:
            return f"Error: body JSON invalid: {e}"

    return f"Error: method invalid, use GET or POST"


