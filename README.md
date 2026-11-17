# LectureLens - Speech-to-Text Summarizer (English)

## Setup
1. Install ffmpeg (needed by Whisper): https://ffmpeg.org/download.html
   (Windows: `winget install ffmpeg`, macOS: `brew install ffmpeg`)
2. `pip install -r requirements.txt`

## Run
    python main.py
Menu 1 = transcribe an audio file, 2 = record from the microphone, 4 = open the report page.
Use short clips (1-3 min) and the "tiny.en" / "base.en" model while testing.

## Output
- `sessions/*.json`  saved transcript, summary, keywords, stats
- `sessions/*_report.html`  web page report with charts (menu 4)
- `sessions/*_report.txt`  plain text report (menu 5)
- `recordings/*.wav`  microphone recordings

## AI summary (optional)
LectureLens can ask Claude (Anthropic API) to write a real summary, vocabulary and concept flow.
1. Create an API key at https://console.anthropic.com (add a little credit first).
2. Run the program, choose 6 (Settings), then 4, and paste the key. It is saved in `api_key.txt`.
3. NEVER upload `api_key.txt` to GitHub (it is listed in `.gitignore`).
Without a key the program still works and uses a simple extractive summary.
