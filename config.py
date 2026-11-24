"""Central settings. Change things here, not in the code."""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "jarvis.db"

# Brain: ollama (free, local) | groq (free key) | gemini (free key) | anthropic (paid)
PROVIDER = os.getenv("JARVIS_PROVIDER", "ollama").lower()

PROVIDERS = {
    "ollama": {"base_url": "http://localhost:11434/v1", "key_env": None, "model": os.getenv("JARVIS_MODEL", "llama3.1:8b")},
    "groq": {"base_url": "https://api.groq.com/openai/v1", "key_env": "GROQ_API_KEY", "model": os.getenv("JARVIS_MODEL", "llama-3.3-70b-versatile")},
    "gemini": {"base_url": "https://generativelanguage.googleapis.com/v1beta/openai/", "key_env": "GEMINI_API_KEY", "model": os.getenv("JARVIS_MODEL", "gemini-2.0-flash")},
    "anthropic": {"base_url": None, "key_env": "ANTHROPIC_API_KEY", "model": os.getenv("JARVIS_MODEL", "claude-sonnet-5-5")},
}
MAX_TOKENS = 1024
MAX_HISTORY_MESSAGES = 40
ASSISTANT_NAME = "Jarvis"
USER_NAME = "Boss"  # how Jarvis addresses you

# Voice
WAKE_WORD = "jarvis"
WHISPER_MODEL = "base.en"       # tiny.en = faster, small.en = more accurate
SAMPLE_RATE = 16000
SILENCE_THRESHOLD = 0.015       # raise if it triggers on background noise
SILENCE_SECONDS = 1.0           # pause length that ends your sentence
MAX_RECORD_SECONDS = 15
FOLLOWUP_WINDOW_SECONDS = 8     # keeps listening after a reply, no wake word needed
TTS_RATE = 185                  # words per minute

SYSTEM_PROMPT = f"""You are {ASSISTANT_NAME}, a personal AI assistant for {USER_NAME}.
Personality: calm, witty, efficient, subtly dry humour. Address the user as "{USER_NAME}" occasionally, not every sentence.
Your replies are SPOKEN ALOUD, so: keep them short (1-3 sentences), no markdown, no bullet points, no emojis.
Use your tools whenever they help. Never claim to have done something unless a tool confirmed it.
If a request is unclear, ask one brief question. If you learn a lasting fact about the user, save it with the remember tool."""