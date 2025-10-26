"""
LLM Client - Handles API calls to language models using httpx
"""
import httpx
import json
from typing import Dict, List, Any, Optional
from core import python_tool


class LLMClient:
    """Client for making API calls to language models"""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the LLM client

        Args:
            config: Configuration dictionary containing:
                - endpoint: API endpoint URL
                - model: Model name
                - headers: HTTP headers including auth
                - temperature: Sampling temperature
                - max_tokens: Maximum tokens to generate
                - top_p: Nucleus sampling parameter
                - enable_python_tool: Whether to enable Python execution tool
        """
        self.endpoint = config['endpoint']
        self.model = config['model']
        self.headers = config['headers']
        self.temperature = config.get("temperature", None)
        self.max_tokens = config.get("max_tokens", None)
        self.top_p = config.get("top_p", None)
        self.timeout = config.get("timeout", 120)
        self.enable_python_tool = config.get('enable_python_tool', False)

    def create_messages(self, system_prompt: str, user_prompt: str) -> List[Dict[str, str]]:
        """Create message array for the API"""
        messages = []

        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })

        messages.append({
            "role": "user",
            "content": user_prompt
        })

        return messages

    def create_tools(self) -> List[Dict[str, Any]]:
        """Create tools definition for function calling"""
        tools = []

        if self.enable_python_tool:
            tools.append(python_tool.tool_desc)

        return tools

    def call(self, system_prompt: str, user_prompt: str, conversation_history: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Make a call to the LLM API

        Args:
            system_prompt: System prompt for the model
            user_prompt: User prompt
            conversation_history: Optional previous messages for multi-turn conversations

        Returns:
            Response dictionary with 'content', 'tool_calls', and 'finish_reason'
        """
        messages = conversation_history if conversation_history else []

        # Add system message if not in history
        if not any(msg.get('role') == 'system' for msg in messages):
            if system_prompt:
                messages.insert(0, {
                    "role": "system",
                    "content": system_prompt
                })

        # Add user message
        messages.append({
            "role": "user",
            "content": user_prompt
        })

        # Prepare request payload
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p
        }

        # Add tools if enabled
        tools = self.create_tools()
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        # Make API call
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                self.endpoint,
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()

        result = response.json()

        # Parse response
        choice = result['choices'][0]
        message = choice['message']

        return {
            'content': message.get('content', ''),
            'tool_calls': message.get('tool_calls', []),
            'finish_reason': choice.get('finish_reason', 'stop'),
            'full_message': message
        }

    def call_with_tools(self, system_prompt: str, user_prompt: str, max_iterations: int = 5) -> Dict[str, Any]:
        """
        Make a call to the LLM with tool execution support

        Args:
            system_prompt: System prompt for the model
            user_prompt: User prompt
            max_iterations: Maximum number of tool call iterations

        Returns:
            Final response dictionary
        """
        from core.python_tool import run_python

        conversation_history = []

        # Add system message
        if system_prompt:
            conversation_history.append({
                "role": "system",
                "content": system_prompt
            })

        # Add initial user message
        conversation_history.append({
            "role": "user",
            "content": user_prompt
        })

        for iteration in range(max_iterations):
            # Make API call with current conversation
            payload = {
                "model": self.model,
                "messages": conversation_history,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
                "top_p": self.top_p
            }

            # Add tools if enabled
            tools = self.create_tools()
            if tools:
                payload["tools"] = tools
                payload["tool_choice"] = "auto"

            # Make API call
            with httpx.Client(timeout=120.0) as client:
                response = client.post(
                    self.endpoint,
                    headers=self.headers,
                    json=payload
                )
                response.raise_for_status()

            result = response.json()
            choice = result['choices'][0]
            message = choice['message']

            # Add assistant message to history
            conversation_history.append(message)

            # Check if there are tool calls
            tool_calls = message.get('tool_calls', [])

            if not tool_calls:
                # No more tool calls, return final response
                return {
                    'content': message.get('content', ''),
                    'tool_calls': [],
                    'finish_reason': choice.get('finish_reason', 'stop'),
                    'conversation_history': conversation_history
                }

            # Execute tool calls
            for tool_call in tool_calls:
                function_name = tool_call['function']['name']
                function_args = json.loads(tool_call['function']['arguments'])

                # Execute the tool
                if function_name == 'run_python':
                    tool_result = run_python(function_args['code'])
                else:
                    tool_result = {"error": f"Unknown tool: {function_name}"}

                # Add tool result to conversation
                conversation_history.append({
                    "role": "tool",
                    "tool_call_id": tool_call['id'],
                    "name": function_name,
                    "content": json.dumps(tool_result)
                })

        # Max iterations reached
        return {
            'content': "Maximum tool iterations reached",
            'tool_calls': [],
            'finish_reason': 'max_iterations',
            'conversation_history': conversation_history
        }
