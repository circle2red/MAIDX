import base64
import logging
import re
import httpx
import json
from typing import Literal, Union
from core.llm_tools.tools_manager import ToolsManager


def parse_code_fences(s):
    # This regex looks for:
    # 1. Three backticks (```) followed by an optional language identifier.
    # 2. Any character (including newlines) non-greedily, until...
    # 3. Three backticks (```) again.
    regexp = r"```(.*?)\n(.*?)\n```"
    matches = re.finditer(regexp, s, re.DOTALL)  # re.DOTALL makes . match newlines

    parsed_fences = []
    for match in matches:
        parsed_fences.append(match.group(2))
    return parsed_fences



class LLMClient:
    """Client for making API calls to language models"""

    def __init__(self, endpoint, model_name, api_key=None, headers=None, tools_manager=None,
                 temperature=None, max_tokens=None, top_p=None, timeout=None, log_llm_call=False):
        """
        Initialize the LLM client

        Args:
            - endpoint: API endpoint URL
            - model: Model name
            - api_key: LLM api key (or be included in headers)
            - headers: HTTP headers
            - tools limit: Limit how much tools can be used
            - temperature: Sampling temperature
            - max_tokens: Maximum tokens to generate
            - top_p: Nucleus sampling parameter
            - timeout: timeout when accessing LLM, leave empty for no timeout
            - log_llm_call: log LLM response
        """

        self.endpoint = endpoint
        self.model_name = model_name
        if type(headers) is str:
            headers = json.loads(headers)
        if not headers:
            headers = {}
        self.headers = headers
        if api_key:
            self.headers['Authorization'] = f"Bearer {api_key}"
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.top_p = top_p
        self.messages = []
        if not tools_manager:
            tools_manager = ToolsManager(python_limit=0, web_fetch_limit=0)
        self.tools_manager = tools_manager
        self.timeout = timeout
        self.log_llm_call = log_llm_call

    def clear_history(self):
        self.messages = []
        self.tools_manager.reset_limit()

    def add_text_message(self, role: Literal["user", "assistant", "system"], msg: str):
        """Add a pure text message to LLM history"""
        self.messages.append({
            "role": role,
            "content": msg,
        })

    def add_image_message(self, role, img_path:str=None, img_b64:Union[bytes,str]=None, detail="high"):
        """
            Add image to LLM history
            - img_path: url (http, https or local path)
            - img_b64: base64-ed image with headers (str or bytes)
            Provide one. if both, img_b64 is used
        """
        if (not img_path) and (not img_b64):
            raise ValueError("Neither img_path nor img_b64 is provided")

        img_url = None
        if img_path:
            if img_path.startswith("http://") or img_path.startswith("https://"):
                img_url = img_path
            else:  # local img
                with open(img_path, 'rb') as f:
                    img_content = f.read()
                img_content = base64.b64encode(img_content).decode('utf-8')
                if img_path.endswith("jpg"):
                    img_url = f'data:image/jpeg;base64,{img_content}'
                elif img_path.endswith("png"):
                    img_url = f"data:image/png;base64,{img_content}"
                elif img_path.endswith("bmp"):
                    img_url = f"data:image/bmp;base64,{img_content}"
                elif img_path.endswith("gif"):
                    img_url = f"data:image/gif;base64,{img_content}"
                else:
                    # defaults to jpg
                    img_url = f'data:image/jpeg;base64,{img_content}'
        if img_b64:
            if type(img_b64) is str:
                img_url = img_b64
            else:
                img_url = img_b64.decode('utf-8')

        self.messages.append({
            "role": role,
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": img_url,
                        "detail": detail
                    }
                }
            ]
        })

    def get_current_msg_list(self):
        return self.messages

    def send_llm_request_once(self, add_to_messages=True, dry_run=False, return_full=True):
        """
        Send current messages to LLM to get a response.
        May return partial response (such as tool call)
        add_to_messages: add to current llm messages
        dry_run: return payload instead
        return_full: Return the full response structure. Set to false for only the response msg (str).
        """
        payload = {
            "model": self.model_name,
            "messages": self.messages,
        }
        if self.temperature:
            payload['temperature'] = self.temperature
        if self.max_tokens:
            payload['max_tokens'] = self.max_tokens
        if self.top_p:
            payload['top_p'] = self.top_p

        if self.tools_manager.has_tools():
            payload['tools'] = self.tools_manager.gen_tools_list_for_llm(add_limits_prompt=True)
            payload['tool_choice'] = "auto"

        if dry_run:
            return payload

        request = httpx.post(
            url=self.endpoint,
            headers=self.headers,
            json=payload,
            timeout=self.timeout,
        )
        resp = request.json()
        if 'error' in resp:
            raise ValueError(f"Error in LLM response: {resp}")
        if self.log_llm_call:
            logging.warning("LLM: " + resp['choices'][0]['message']['content'])
        if add_to_messages:
            self.messages.append(resp['choices'][0]['message'])

        if return_full:
            return resp
        else:
            return resp['choices'][0]['message']['content']

    def send_llm_request(self, return_full=False, max_rounds=-1):
        """
        Send current messages to LLM to ensure a final answer.
        params:
        return_full: Return the full response structure. Set to false for only the response msg (str).
        max_rounds: Specify how many rounds of LLM to be called, default unlimited
        """
        while max_rounds:  # != 0
            resp = self.send_llm_request_once(add_to_messages=True)
            msg = resp['choices'][0]['message']
            finish_reason = resp['choices'][0]["finish_reason"]
            if finish_reason == "tool_calls" or finish_reason == "function_call":
                tool_result = self.tools_manager.execute_tool_from_llm_msg(msg)
                self.messages.append(tool_result)
            elif finish_reason == "stop" or finish_reason == "length":
                if return_full:
                    return resp
                return msg['content']
            else:  # "content_filter" or Null
                return ""
            max_rounds -= 1
        return ""

    def pretty_print_messages(self):
        """Return pretty-printed LLM communication message"""
        for msg in self.messages:
            print(f"{msg['role']}: {msg['content']}")
            print("\n\n")


# debug test
if __name__ == '__main__':
    logging.basicConfig(level=logging.WARNING)
    import dotenv
    import os
    dotenv.load_dotenv()
    # print(os.environ.values())

    a = LLMClient(
        endpoint=os.getenv("LLM_API"),
        model_name=os.getenv("LLM_MODEL"),
        api_key=os.getenv("LLM_KEY"),
        tools_manager=ToolsManager(python_limit=3, web_fetch_limit=1),
        timeout=120,
    )

    a.add_text_message("system", "You are a helpful assistant.")
    a.add_text_message("user",
                       "Use the tools to calculate: What is the day and date of 1942 days after "
                       "3rd September 2013?")
    a.add_text_message("user", "What is this website about: "
                               "https://www.hko.gov.hk/textonly/v2/forecast/chinesewx2.htm")


