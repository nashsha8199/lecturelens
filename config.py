"""config.py - constants for LectureLens (English only)."""

SESSIONS_DIR = "sessions"      # one JSON file per transcribed recording
RECORDINGS_DIR = "recordings"  # microphone recordings are saved here
SAMPLE_RATE = 16000            # Whisper works best with 16 kHz audio

# Set of audio/video types we accept (Whisper uses ffmpeg to read them)
VALID_AUDIO = {".wav", ".mp3", ".m4a", ".mp4", ".flac", ".ogg", ".webm"}

# tuple: English-only Whisper models (bigger = slower but more accurate)
WHISPER_MODELS = ("tiny.en", "base.en", "small.en")

# dict: user settings that can be changed in the menu
DEFAULT_SETTINGS = {
    "model": "base.en",
    "summary_sentences": 5,
    "keywords": 10,
}

# set: common English words we ignore when counting keywords
ENGLISH_STOPWORDS = {
    "a", "about", "above", "after", "again", "all", "also", "am", "an", "and", "any",
    "are", "as", "at", "be", "because", "been", "before", "being", "below", "between",
    "both", "but", "by", "can", "could", "did", "do", "does", "doing", "down", "during",
    "each", "few", "for", "from", "further", "get", "got", "had", "has", "have", "having",
    "he", "her", "here", "hers", "him", "his", "how", "i", "if", "in", "into", "is", "it",
    "its", "just", "like", "me", "more", "most", "my", "no", "nor", "not", "now", "of",
    "off", "on", "once", "only", "or", "other", "our", "ours", "out", "over", "own",
    "really", "same", "she", "should", "so", "some", "such", "than", "that", "the",
    "their", "theirs", "them", "then", "there", "these", "they", "this", "those",
    "through", "to", "too", "under", "until", "up", "very", "was", "we", "were", "what",
    "when", "where", "which", "while", "who", "whom", "why", "will", "with", "would",
    "you", "your", "yours", "yeah", "okay", "going", "know", "think", "right", "well",
    "gonna", "let", "one", "say", "see", "thing", "things", "something",
}
