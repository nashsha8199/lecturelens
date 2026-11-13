"""main.py - LectureLens: speech-to-text summarizer (menu and program flow)."""
import os

from config import DEFAULT_SETTINGS, WHISPER_MODELS
import transcribe
import analyze
import storage
import visualize


# ---------- helpers ----------
def ask_int(prompt, default, low=1, high=10_000):
    """Ask for an integer in [low, high]; fall back to default if invalid."""
    text = input(prompt).strip()
    if text.isdigit() and low <= int(text) <= high:
        return int(text)
    print(f"  Invalid number, using {default}.")
    return default


def print_session(session):
    """Show summary, keywords and stats of one session."""
    print(f"\n=== {session['name']} ({session['created']}) ===")
    print("\nSummary:")
    if session["summary"]:
        for sentence in session["summary"]:
            print(f"  - {sentence}")
    else:
        print("  (not enough text to summarize)")
    print("\nKeywords:", ", ".join(w for w, _ in session["keywords"]) or "(none)")
    stats = session["stats"]
    print(f"\nDuration {stats['duration']} | {stats['words']} words | "
          f"{stats['words_per_min']} words/min | {stats['unique_words']} unique words")


def choose_session():
    """Let the user pick one saved session from a numbered list."""
    sessions = storage.list_sessions()
    if not sessions:
        print("  No saved sessions yet.")
        return None
    for i, s in enumerate(sessions, start=1):
        print(f"  {i}) {s['name']}  [{s['created']}, {s['stats']['duration']}]")
    pick = input("Choose a session (Enter to cancel): ").strip()
    if pick.isdigit() and 1 <= int(pick) <= len(sessions):
        return sessions[int(pick) - 1]
    return None


# ---------- main workflow ----------
def process_audio(path, settings, name=""):
    """Transcribe -> analyze -> save. Returns the new session or None."""
    result = transcribe.transcribe_audio(path, settings["model"])
    if result is None:
        return None
    if not result["segments"]:
        print("  No speech detected in this audio.")
        return None

    summary = analyze.summarize(result["segments"], settings["summary_sentences"])
    keywords = analyze.top_keywords(result["segments"], settings["keywords"])
    stats = analyze.get_stats(result)

    if not name:
        name = os.path.splitext(os.path.basename(path))[0]
    session = storage.make_session(name, path, result, summary, keywords, stats)
    storage.save_session(session)
    print_session(session)
    return session


def action_transcribe_file(settings):
    path = input("Path to audio file: ").strip().strip('"')
    if not transcribe.is_valid_audio(path):
        print("  File not found or unsupported type.")
        return
    session = process_audio(path, settings)
    if session and input("\nShow charts? (y/n): ").strip().lower() == "y":
        visualize.show_dashboard(session)


def action_record(settings):
    seconds = ask_int("Seconds to record [30]: ", 30, 3, 600)
    path = transcribe.record_audio(seconds)
    if path is None:
        return
    name = input("Name for this recording (optional): ").strip()
    session = process_audio(path, settings, name)
    if session and input("\nShow charts? (y/n): ").strip().lower() == "y":
        visualize.show_dashboard(session)


def action_view(show_charts=False):
    session = choose_session()
    if session is None:
        return
    if show_charts:
        visualize.show_dashboard(session)
    else:
        print_session(session)
        if input("\nShow full transcript? (y/n): ").strip().lower() == "y":
            for start, _, text in session["segments"]:
                print(f"  [{analyze.format_time(start)}] {text}")


def action_export():
    session = choose_session()
    if session is not None:
        print(f"  Report saved to {storage.export_report(session)}")


def action_settings(settings):
    print("\nCurrent settings:")
    for key, value in settings.items():
        print(f"  {key}: {value}")
    print("\n1) Whisper model  2) Summary length  3) Number of keywords  0) Back")
    choice = input("Choose: ").strip()

    if choice == "1":
        print("  Options:", ", ".join(WHISPER_MODELS), "(tiny.en = fastest, small.en = most accurate)")
        model = input("Model: ").strip().lower()
        if model in WHISPER_MODELS:
            settings["model"] = model
        else:
            print("  Unknown model.")
    elif choice == "2":
        settings["summary_sentences"] = ask_int("Summary sentences (1-15): ", 5, 1, 15)
    elif choice == "3":
        settings["keywords"] = ask_int("Keywords to show (3-25): ", 10, 3, 25)


def print_menu():
    print("\n===== LectureLens =====")
    print("1) Transcribe an audio file")
    print("2) Record from microphone")
    print("3) View a saved session")
    print("4) Show charts for a session")
    print("5) Export a session report (.txt)")
    print("6) Settings")
    print("0) Quit")


def main():
    settings = dict(DEFAULT_SETTINGS)
    while True:
        print_menu()
        choice = input("Choose: ").strip()

        if choice == "1":
            action_transcribe_file(settings)
        elif choice == "2":
            action_record(settings)
        elif choice == "3":
            action_view()
        elif choice == "4":
            action_view(show_charts=True)
        elif choice == "5":
            action_export()
        elif choice == "6":
            action_settings(settings)
        elif choice == "0":
            print("Goodbye!")
            break
        else:
            print("  Invalid choice.")


if __name__ == "__main__":
    main()
