"""transcribe.py - recording audio and speech-to-text with Whisper (English)."""
import os
from datetime import datetime

from config import SAMPLE_RATE, RECORDINGS_DIR, VALID_AUDIO

_model_cache = {}  # dict: model name -> loaded Whisper model (loading is slow)


def is_valid_audio(path):
    """Check that the file exists and has an accepted extension."""
    ext = os.path.splitext(path)[1].lower()
    return os.path.isfile(path) and ext in VALID_AUDIO


def record_audio(seconds):
    """Record from the default microphone and save a .wav file. Returns its path."""
    try:
        import sounddevice as sd
        from scipy.io import wavfile
    except ImportError:
        print("  Recording needs: pip install sounddevice scipy")
        return None

    os.makedirs(RECORDINGS_DIR, exist_ok=True)
    path = os.path.join(RECORDINGS_DIR, datetime.now().strftime("rec_%Y%m%d_%H%M%S.wav"))
    print(f"  Recording {seconds} seconds... speak now!")
    data = sd.rec(int(seconds * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype="int16")
    sd.wait()
    wavfile.write(path, SAMPLE_RATE, data)
    print(f"  Saved {path}")
    return path


def load_whisper(model_name):
    """Load (and cache) a Whisper model."""
    if model_name not in _model_cache:
        import whisper
        print(f"  Loading Whisper '{model_name}' model (first time downloads it)...")
        _model_cache[model_name] = whisper.load_model(model_name)
    return _model_cache[model_name]


def transcribe_audio(path, model_name="base.en"):
    """Transcribe an English audio file.

    Returns a dict: {"text": str, "segments": [(start, end, text), ...]}
    or None if Whisper is not installed.
    """
    try:
        model = load_whisper(model_name)
    except ImportError:
        print("  Whisper is not installed. Run: pip install openai-whisper  (and install ffmpeg)")
        return None

    print("  Transcribing... (long audio can take a while on CPU)")
    result = model.transcribe(path, language="en", fp16=False)

    # list of tuples (start seconds, end seconds, text)
    segments = [(seg["start"], seg["end"], seg["text"].strip())
                for seg in result["segments"] if seg["text"].strip()]
    return {"text": result["text"].strip(), "segments": segments}
