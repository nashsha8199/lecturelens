# LectureLens - Speech-to-Text Summarizer (English)

## Setup
1. Install ffmpeg (needed by Whisper): https://ffmpeg.org/download.html
   (Windows: `winget install ffmpeg`, macOS: `brew install ffmpeg`)
2. `pip install -r requirements.txt`

## Run
    python main.py
Menu 1 = transcribe an audio file, 2 = record from the microphone.
Use short clips (1-3 min) and the "tiny.en" / "base.en" model while testing.

## Output
- `sessions/*.json`  saved transcript, summary, keywords, stats
- `sessions/*_report.txt`  readable report (menu 5)
- `recordings/*.wav`  microphone recordings
