"""Voice I/O: microphone -> Whisper (speech-to-text), and pyttsx3 (text-to-speech)."""
import time

import numpy as np
import sounddevice as sd

import config


class Voice:
    def __init__(self):
        from faster_whisper import WhisperModel
        import pyttsx3

        print("Loading speech model (first run downloads it)...")
        self.stt = WhisperModel(config.WHISPER_MODEL, compute_type="int8")
        self.tts = pyttsx3.init()
        self.tts.setProperty("rate", config.TTS_RATE)

    def listen(self, wait_timeout=None, abort=None, on_start=None):
        """Record one utterance.

        Returns an audio array, or None if nobody spoke within wait_timeout
        or abort() became true (used when a typed command arrives).
        """
        block = int(config.SAMPLE_RATE * 0.1)
        chunks, started, silent_blocks = [], False, 0
        t0 = time.time()
        with sd.InputStream(samplerate=config.SAMPLE_RATE, channels=1, dtype="float32") as stream:
            while True:
                data, _ = stream.read(block)
                loud = float(np.sqrt(np.mean(data**2))) > config.SILENCE_THRESHOLD
                if loud and not started:
                    started = True
                    if on_start:
                        on_start()
                if started:
                    chunks.append(data)
                    silent_blocks = 0 if loud else silent_blocks + 1
                    if silent_blocks * 0.1 >= config.SILENCE_SECONDS:
                        break
                    if len(chunks) * 0.1 >= config.MAX_RECORD_SECONDS:
                        break
                else:
                    if wait_timeout and time.time() - t0 > wait_timeout:
                        return None
                    if abort and abort():
                        return None
        return np.concatenate(chunks).flatten()

    def transcribe(self, audio) -> str:
        if audio is None or len(audio) < config.SAMPLE_RATE * 0.3:
            return ""
        segments, _ = self.stt.transcribe(audio, language="en", beam_size=1, vad_filter=True)
        return " ".join(s.text.strip() for s in segments).strip()

    def speak(self, text: str):
        print(f"{config.ASSISTANT_NAME}: {text}")
        self.tts.say(text)
        self.tts.runAndWait()