"""Jarvis entry point.

  python main.py --voice   -> wake word + voice, and opens the Jarvis screen in your browser
  python main.py --ui      -> Jarvis screen only (type to talk, the browser speaks the replies)
  python main.py           -> plain terminal chat
"""
import argparse
import time
import webbrowser

import config
from core.brain import BaseBrain, create_brain
from tools import registry
from ui.server import UIState, start_server


def greeting() -> str:
    hour = time.localtime().tm_hour
    part = "morning" if hour < 12 else "afternoon" if hour < 18 else "evening"
    return f"Good {part}, {config.USER_NAME}. {config.ASSISTANT_NAME} is online."


def think(brain: BaseBrain, ui: UIState, text: str, confirm, show_user=True) -> str:
    """Send text to the brain and keep the screen in sync. Never crashes the app."""
    if show_user:
        ui.add("user", text)
    ui.set(status="thinking")
    try:
        reply = brain.chat(text, confirm)
    except Exception as e:
        print(f"[error] {e}")
        reply = "Sorry, I hit a problem reaching my brain. Please check that Ollama is still running."

    ui.add("jarvis", reply)
    return reply


# ---------------------------------------------------------------- terminal only
def terminal_confirm(question: str) -> bool:
    return input(f"  ? {question} (y/n): ").strip().lower().startswith("y")


def run_text(brain: BaseBrain):
    print(f"{config.ASSISTANT_NAME} online (text mode). Type 'quit' to exit.\n")
    while True:
        try:
            user = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if user.lower() in {"quit", "exit"}:
            break
        if user:
            print(f"{config.ASSISTANT_NAME}: {brain.chat(user, terminal_confirm)}\n")


# ---------------------------------------------------------------- browser screen only
def run_ui(brain: BaseBrain, ui: UIState):
    ui.set(browser_speech=True, status="idle")
    ui.add("jarvis", greeting())
    print("Jarvis screen is running. Press Ctrl+C here to stop.")
    try:
        while True:
            text = ui.pop_input(timeout=0.5)
            if text:
                think(brain, ui, text, ui.ask, show_user=False)

                ui.set(status="idle")
    except KeyboardInterrupt:
        pass


# ---------------------------------------------------------------- voice (+ optional screen)
def run_voice(brain: BaseBrain, ui: UIState):
    from core.voice import Voice

    voice = Voice()

    def speak(text: str):
        ui.set(status="speaking")
        voice.speak(text)
        ui.set(status="idle")

    def voice_confirm(question: str) -> bool:
        ui.add("jarvis", question)
        speak(question)
        ui.set(status="listening")
        answer = voice.transcribe(voice.listen(wait_timeout=6)).lower()
        ui.set(status="thinking")
        return any(w in answer for w in ("yes", "yeah", "sure", "do it", "confirm"))

    hello = f"{config.ASSISTANT_NAME} online. Say my name when you need me."
    ui.add("jarvis", hello)
    speak(hello)
    active_until = 0.0

    while True:
        # commands typed into the browser
        typed = ui.pop_input()

        if typed:
            speak(think(brain, ui, typed, voice_confirm, show_user=False))
            active_until = time.time() + config.FOLLOWUP_WINDOW_SECONDS
            continue

        in_conversation = time.time() < active_until
        ui.set(status="listening" if in_conversation else "idle")
        audio = voice.listen(
            wait_timeout=3 if in_conversation else None,
            abort=ui.has_input,
            on_start=lambda: ui.set(status="listening"),
        )
        if audio is None:
            continue

        text = voice.transcribe(audio)
        if not text:
            continue
        print(f"You: {text}")

        if not in_conversation:
            lowered = text.lower()
            if config.WAKE_WORD not in lowered:
                continue  # ignore everything without the wake word
            text = lowered.split(config.WAKE_WORD, 1)[1].strip(" ,.!?")
            if not text:
                ui.add("jarvis", "Yes?")
                speak("Yes?")
                active_until = time.time() + config.FOLLOWUP_WINDOW_SECONDS
                continue

        if any(p in text.lower() for p in ("goodbye", "shut down", "go to sleep")):

            ui.add("jarvis", "Goodbye.")
            speak("Goodbye.")
            break

        speak(think(brain, ui, text, voice_confirm))
        active_until = time.time() + config.FOLLOWUP_WINDOW_SECONDS


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--voice", action="store_true", help="voice mode (also opens the Jarvis screen)")
    parser.add_argument("--ui", action="store_true", help="Jarvis screen only, typing instead of voice")
    parser.add_argument("--no-screen", action="store_true", help="with --voice: do not open the browser")
    args = parser.parse_args()

    try:
        brain = create_brain(registry)
    except RuntimeError as e:
        print(f"\nSetup problem: {e}")
        return
    model = config.PROVIDERS[config.PROVIDER]["model"]
    print(f"Brain: {config.PROVIDER} / {model}")

    if not (args.voice or args.ui):
        return run_text(brain)

    ui = UIState(f"{config.PROVIDER.upper()} · {model}")
    if args.ui or not args.no_screen:
        url = start_server(ui)
        print(f"Jarvis screen: {url}")
        webbrowser.open_new_tab(url)


    run_ui(brain, ui) if args.ui else run_voice(brain, ui)


if __name__ == "__main__":
    main()ch