"""transcribe.py - recording audio and speech-to-text with Whisper (English)."""
import os
import subprocess
import sys
from datetime import datetime

from config import SAMPLE_RATE, RECORDINGS_DIR, VALID_AUDIO

_model_cache = {}  # dict: model name -> loaded Whisper model (loading is slow)


def is_valid_audio(path):
    """Check that the file exists and has an accepted extension."""
    ext = os.path.splitext(path)[1].lower()
    return os.path.isfile(path) and ext in VALID_AUDIO


def clean_path(text):
    """Clean a path typed or dragged into Terminal: remove quotes and backslashes before spaces."""
    text = text.strip().strip('"').strip("'")   # remove spaces and quote marks around the path
    return text.replace("\\ ", " ")              # Terminal writes "my\ file.mp3" for spaces, undo that


def browse_for_file():
    """Open the Mac file window so the user can click on the audio file.

    Returns the chosen path, or "" if the user cancelled or this is not a Mac.
    """
    if sys.platform != "darwin":                 # darwin = macOS
        print("  File window only works on a Mac, please type the path instead.")
        return ""
    # ask macOS itself to show its normal "choose a file" window
    script = 'POSIX path of (choose file with prompt "Choose an audio file")'
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if result.returncode != 0:                   # the user pressed Cancel
        return ""
    return result.stdout.strip()                 # the chosen path, without the line break


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
