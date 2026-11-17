"""storage.py - save / load sessions as JSON files and export reports."""
import json
import os
from datetime import datetime

from config import SESSIONS_DIR
import analyze


def make_session(name, audio_path, result, summary, keywords, stats, ai=None):
    """Bundle everything about one recording into a dict."""
    return {
        "id": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "name": name,
        "audio": audio_path,
        "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "text": result["text"],
        "segments": result["segments"],
        "summary": summary,
        "keywords": keywords,
        "stats": stats,
        "ai": ai,          # AI-written summary (a dict) or None if not made yet
    }


def save_session(session):
    os.makedirs(SESSIONS_DIR, exist_ok=True)
    path = os.path.join(SESSIONS_DIR, f"{session['id']}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(session, f, ensure_ascii=False, indent=2)
    return path


def list_sessions():
    """Return all saved sessions (newest first)."""
    if not os.path.isdir(SESSIONS_DIR):
        return []
    sessions = []
    for filename in sorted(os.listdir(SESSIONS_DIR), reverse=True):
        if filename.endswith(".json"):
            with open(os.path.join(SESSIONS_DIR, filename), encoding="utf-8") as f:
                sessions.append(json.load(f))
    return sessions


def export_report(session):
    """Write a readable .txt report next to the session file. Returns its path."""
    os.makedirs(SESSIONS_DIR, exist_ok=True)
    path = os.path.join(SESSIONS_DIR, f"{session['id']}_report.txt")
    lines = [f"LectureLens report: {session['name']}",
             f"Created: {session['created']}",
             "", "== SUMMARY =="]
    ai = session.get("ai")
    if ai:                                     # AI summary first, if we have one
        lines += [ai["tldr"], ""]
        lines += [f"- {point}" for point in ai["takeaways"]]
    else:
        lines += [f"- {s}" for s in session["summary"]]
    lines += ["", "== KEYWORDS =="]
    lines.append(", ".join(w for w, _ in session["keywords"]))
    lines += ["", "== STATS =="]
    lines += [f"{k}: {v}" for k, v in session["stats"].items()]
    lines += ["", "== FULL TRANSCRIPT =="]
    for start, _, text in session["segments"]:
        lines.append(f"[{analyze.format_time(start)}] {text}")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return path
