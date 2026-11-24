# Jarvis - personal AI assistant

## Setup
```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # then paste your Anthropic API key into .env
```

## Run
```bash
python main.py            # text mode - start here
python main.py --voice    # voice mode, say "Jarvis, what time is it?"
```

## Add a new tool (2 minutes)
Create a function in any file inside `tools/` and decorate it:

```python
from tools.registry import registry

@registry.register("tell_joke", "Tell the user a joke.")
def tell_joke():
    return "Why do programmers prefer dark mode? Because light attracts bugs."
```
Then import the file in `tools/__init__.py`. Use `confirm=True` for anything risky.

## Troubleshooting
- Wakes up on noise / ignores you: tune SILENCE_THRESHOLD in config.py.
- Poor recognition: set WHISPER_MODEL = "small.en".
- Linux TTS needs: sudo apt install espeak-ng
