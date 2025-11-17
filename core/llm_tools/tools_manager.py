import copy
import json
from typing import List

from core.llm_tools import python_tool, web_fetch_tool, think_tool


class ToolsManager:
    """Manager for LLM tools"""

    def __init__(self, python_limit=5, web_fetch_limit=5, think_limit=5):
        """
        Set up a ToolsManager. Set both limits to 0 to disallow any tools.
        """
        self.tools = {}
        self.tools[python_tool.tool_desc['function']['name']] = {
            'desc': python_tool.tool_desc,
            'usage_limit': python_limit,
            'func': python_tool.run_python,
            'init_limit': python_limit,
        }
        self.tools[web_fetch_tool.tool_desc['function']['name']] = {
            'desc': web_fetch_tool.tool_desc,
            'usage_limit': web_fetch_limit,
            'func': web_fetch_tool.web_fetch,
            'init_limit': web_fetch_limit,
        }
        self.tools[think_tool.tool_desc['function']['name']] = {
            'desc': think_tool.tool_desc,
            'usage_limit': think_limit,
            'func': think_tool.think,
            'init_limit': think_limit,
        }
        """
            format: {
                "tool_name": {
                    "desc": tool_desc,
                    "usage_limit": 1,
                    "func": callable,
                    "init_limit": 3,
                }
            }
        """

    def has_tools(self):
        """Returns a bool indicating if any tool is available"""
        for tool_name, tool in self.tools.items():
            if tool['usage_limit'] > 0:
                return True
        return False

    def reset_limit(self):
        for tool_name, tool in self.tools.items():
            tool['usage_limit'] = tool['init_limit']

    def gen_tools_list_for_llm(self, add_limits_prompt=True) -> List:
        """
        Generate LLM tool list
        Format: [tooldesc1, tooldesc2, ...]
        """
        res = []
        for tool_name, tool in self.tools.items():
            # Don't let the LLM see the tool if it is not allowed in the first place.
            if tool['init_limit'] == 0:
                continue
            if tool['usage_limit'] > 0:
                desc = tool['desc']
                if add_limits_prompt:
                    desc = copy.deepcopy(tool['desc'])
                    desc['function']['description'] += f"\n\nYou have {tool['usage_limit']} " \
                                                       f"calls to this tool left."
                res.append(desc)
            else:
                # If the LLM has seen the tool, it has to be provided throughout the conversation.
                desc = copy.deepcopy(tool['desc'])
                desc['function']['description'] = f"Currently you don't have access to this tool."
                res.append(desc)

        return res

    def execute_tool_from_llm_msg(self, llm_resp):
        """
        Take a LLM response and execute tool, then generate the msg (role: tool) for llm.
        Input: LLM_resp['choices'][0]['message']
        Output: A ready to append {'role': 'tool', ...}
        """
        tool_call = llm_resp['tool_calls'][0]
        func = tool_call['function']
        tool_exec_result = ""
        tool_name = func['name']
        if tool_name in self.tools:
            if self.tools[tool_name]['usage_limit'] > 0:
                self.tools[tool_name]['usage_limit'] -= 1
                argument = json.loads(func['arguments'])
                tool_exec_result = self.tools[tool_name]['func'](**argument)
            else:
                tool_exec_result = f"Error: call {tool_name} exceeded."
        else:
            tool_exec_result = f"Error: {tool_name} not found."

        return {
            "role": "tool",
            "tool_call_id": tool_call['id'],
            "content": str(tool_exec_result)
        }





