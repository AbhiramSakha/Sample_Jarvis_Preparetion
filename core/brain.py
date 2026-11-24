"""The brain: a tool-use loop that works with several AI providers."""
import json
import os
import urllib.request

import config
from core.memory import memory


class BaseBrain:
    def __init__(self, registry):
        self.registry = registry
        self.history = []

    def _system(self):
        facts = memory.all_facts()
        known = "\n".join(f"- {k}: {v}" for k, v in facts.items()) or "(nothing yet)"
        return f"{config.SYSTEM_PROMPT}\n\nThings you know about the user:\n{known}"

    def _trim(self):
        """Drop old messages, but only cut at a plain user message so tool pairs stay intact."""
        if len(self.history) <= config.MAX_HISTORY_MESSAGES:
            return
        for i in range(len(self.history) - config.MAX_HISTORY_MESSAGES, len(self.history)):
            msg = self.history[i]
            if msg["role"] == "user" and isinstance(msg["content"], str):
                self.history = self.history[i:]
                return

    def chat(self, user_text: str, confirm_fn) -> str:
        raise NotImplementedError



class OpenAICompatBrain(BaseBrain):
    """Ollama (local, free), Groq, Gemini - all speak the same API."""

    def __init__(self, registry):
        super().__init__(registry)
        from openai import OpenAI

        cfg = config.PROVIDERS[config.PROVIDER]
        self.model = cfg["model"]
        key = os.getenv(cfg["key_env"]) if cfg["key_env"] else "ollama"
        if not key:
            raise RuntimeError(
                f"Missing {cfg['key_env']}. Add it to your .env file, "
                "or switch to the free local option: JARVIS_PROVIDER=ollama"
            )
        if config.PROVIDER == "ollama":
            self._check_ollama()
        self.client = OpenAI(base_url=cfg["base_url"], api_key=key)

    def _check_ollama(self):
        try:
            with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=3) as r:
                models = [m["name"] for m in json.load(r).get("models", [])]
        except Exception:
            raise RuntimeError(
                "Ollama is not running. Install it from https://ollama.com, then run:\n"
                f"    ollama pull {self.model}\n"
                "and start this program again."
            )
        if not any(m == self.model or m.startswith(self.model.split(":")[0] + ":") and self.model in m for m in models):
            raise RuntimeError(f"Model not downloaded yet. Run:  ollama pull {self.model}")


    def chat(self, user_text, confirm_fn):
        self.history.append({"role": "user", "content": user_text})
        self._trim()

        for _ in range(8):
            resp = self.client.chat.completions.create(
                model=self.model,
                max_tokens=config.MAX_TOKENS,
                messages=[{"role": "system", "content": self._system()}] + self.history,
                tools=self.registry.openai_schemas(),
            )
            msg = resp.choices[0].message

            if not msg.tool_calls:
                text = (msg.content or "").strip()
                self.history.append({"role": "assistant", "content": text})
                return text

            self.history.append(
                {
                    "role": "assistant",
                    "content": msg.content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {"name": tc.function.name, "arguments": tc.function.arguments or "{}"},
                        }
                        for tc in msg.tool_calls
                    ],
                }

            )
            for tc in msg.tool_calls:
                try:
                    args = json.loads(tc.function.arguments or "{}")
                except json.JSONDecodeError:
                    args = {}
                print(f"  [tool] {tc.function.name} {args}")
                out = self.registry.run(tc.function.name, args, confirm_fn)
                self.history.append({"role": "tool", "tool_call_id": tc.id, "content": out})

        return "I got stuck in a loop on that one. Could you rephrase?"


class AnthropicBrain(BaseBrain):
    """Claude (needs a paid API key, and: pip install anthropic)."""

    def __init__(self, registry):
        super().__init__(registry)
        import anthropic

        if not os.getenv("ANTHROPIC_API_KEY"):
            raise RuntimeError("Missing ANTHROPIC_API_KEY in your .env file.")
        self.client = anthropic.Anthropic()
        self.model = config.PROVIDERS["anthropic"]["model"]

    def chat(self, user_text, confirm_fn):
        self.history.append({"role": "user", "content": user_text})
        self._trim()

        for _ in range(8):
            resp = self.client.messages.create(
                model=self.model,

                max_tokens=config.MAX_TOKENS,
                system=self._system(),
                tools=self.registry.schemas(),
                messages=self.history,
            )
            self.history.append({"role": "assistant", "content": resp.content})
            if resp.stop_reason != "tool_use":
                return "".join(b.text for b in resp.content if b.type == "text").strip()

            results = []
            for block in resp.content:
                if block.type == "tool_use":
                    print(f"  [tool] {block.name} {block.input}")
                    out = self.registry.run(block.name, block.input, confirm_fn)
                    results.append({"type": "tool_result", "tool_use_id": block.id, "content": out})
            self.history.append({"role": "user", "content": results})

        return "I got stuck in a loop on that one. Could you rephrase?"


def create_brain(registry):
    if config.PROVIDER not in config.PROVIDERS:
        raise RuntimeError(f"Unknown provider '{config.PROVIDER}'. Choose: {', '.join(config.PROVIDERS)}")
    if config.PROVIDER == "anthropic":
        return AnthropicBrain(registry)
    return OpenAICompatBrain(registry)