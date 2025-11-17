tool_desc = {
    "type": "function",
    "function": {
        "name": "think_tool",
        "description": "Use this tool to think internally. \n"
                       "All your thoughts here will not be presented the output, "
                       "and you can decide what conclusions will be made. \n",
        "parameters": {
            "type": "object",
            "properties": {
                "thoughts": {
                    "type": "string",
                    "description": "Your internal thoughts",
                },
                "conclusion": {
                    "type": "string",
                    "description": "Conclusion of your thought, will be returned to you as the call result."
                }
            },
            "required": []
        },
    }
}


def think(thoughts: str = None, conclusion: str = None) -> str:
    if conclusion:
        return conclusion
    else:
        return ""
