# Jarvis - personal AI assistant

## Setup
```bash
python -m venv venv
```

Windows:

```powershell
venv\Scripts\activate
```

**03 — Install Dependencies**

```bash
pip install -r requirements.txt
```

**04 — Install Ollama**

Download: https://ollama.com/download

Pull a local model:

```bash
ollama pull llama3.2
```

**05 — Configure Environment**

```powershell
copy .env.example .env
```

For local AI:

```env
AI_PROVIDER=ollama
OLLAMA_MODEL=llama3.2
OLLAMA_BASE_URL=http://localhost:11434
```

For Anthropic:

```env
AI_PROVIDER=anthropic
ANTHROPIC_API_KEY=your_api_key
```

**06 — Activate JARVIS**

Text mode:

```bash
python main.py
```

Voice mode:

```bash
python main.py --voice
```

## ◈ EXTENSIBILITY

JARVIS supports custom tools through a simple decorator-based registry.

```python
from tools.registry import registry

@registry.register("tell_joke", "Tell the user a joke.")
def tell_joke():
    return "Why do programmers prefer dark mode? Because light attracts bugs."
```

Import the tool inside `tools/__init__.py` to register it.

## ◈ PROJECT STRUCTURE

```text
JARVIS/
├── main.py
├── config.py
├── requirements.txt
├── .env.example
├── tools/
│   ├── __init__.py
│   └── registry.py
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── script.js
└── README.md
```

## ◈ ROADMAP

- [x] Core Python assistant
- [x] Extensible tool registry
- [ ] Ollama local AI integration
- [ ] Anthropic cloud AI integration
- [ ] Animated holographic interface
- [ ] Real-time voice visualization
- [ ] Desktop assistant application
- [ ] Advanced system automation

## ◈ DEVELOPER

**Sakha Abhiram**

GitHub: [@AbhiramSakha](https://github.com/AbhiramSakha)

---

<p align="center">
  <strong>J.A.R.V.I.S — INTELLIGENCE. REDEFINED.</strong>
  <br/>
  <sub>Built for a smarter tomorrow.</sub>
</p>
