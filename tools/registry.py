"""Tiny tool registry: register a Python function and the AI can call it."""


class ToolRegistry:
    def __init__(self):
        self._tools = {}

    def register(self, name, description, properties=None, required=None, confirm=False):
        """Decorator. confirm=True asks the user to approve before the tool runs."""

        def decorator(fn):
            self._tools[name] = {
                "fn": fn,
                "confirm": confirm,
                "schema": {
                    "name": name,
                    "description": description,
                    "input_schema": {
                        "type": "object",
                        "properties": properties or {},
                        "required": required or [],
                    },
                },
            }
            return fn

        return decorator

    def schemas(self):
        return [t["schema"] for t in self._tools.values()]

    def openai_schemas(self):

        """Same tools in the OpenAI/Ollama/Groq/Gemini function-calling format."""
        return [
            {
                "type": "function",
                "function": {
                    "name": t["schema"]["name"],
                    "description": t["schema"]["description"],
                    "parameters": t["schema"]["input_schema"],
                },
            }
            for t in self._tools.values()
        ]

    def run(self, name, args, confirm_fn):
        tool = self._tools.get(name)
        if not tool:
            return f"Error: unknown tool '{name}'."
        if tool["confirm"] and not confirm_fn(f"Run '{name}' with {args}?"):
            return "The user declined this action."
        try:
            return str(tool["fn"](**args))
        except Exception as e:  # never crash the assistant because a tool failed
            return f"Tool error: {e}"


registry = ToolRegistry()