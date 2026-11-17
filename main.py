"""main.py - LectureLens: speech-to-text summarizer (menu and program flow)."""
import os
import webbrowser

from config import DEFAULT_SETTINGS, WHISPER_MODELS
import transcribe
import analyze
import storage
import ai_summary
import report


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
    ai = session.get("ai")
    if ai:                                           # the AI summary is nicer, so show it first
        print("\nSummary (AI):")
        print(f"  {ai['tldr']}")
        for point in ai["takeaways"]:
            print(f"  - {point}")
    else:
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


def add_ai(session):
    """Ask Claude for a summary if this session does not have one yet. True if one was added."""
    if session.get("ai"):                            # already has an AI summary
        return False
    session["ai"] = ai_summary.ai_summarize(session["text"])
    return session["ai"] is not None


def open_report(session):
    """Make the web page report and open it in the browser."""
    if add_ai(session):                              # older sessions get their AI summary now
        storage.save_session(session)                # save it so we only ask once
    path = report.export_html(session)
    print(f"  Report page saved to {path}")
    # os.path.abspath gives the full path, which the browser needs
    webbrowser.open("file://" + os.path.abspath(path))
    print("  Opening it in your browser...")


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
    add_ai(session)                                  # AI summary (skipped if there is no API key)
    storage.save_session(session)
    print_session(session)
    return session


def action_transcribe_file(settings):
    path = input("Path to audio file (press Enter to browse for it): ")
    if path.strip() == "":                  # nothing typed, so open the file window
        path = transcribe.browse_for_file()
    path = transcribe.clean_path(path)      # fix quotes and backslashes from drag and drop
    if not transcribe.is_valid_audio(path):
        print("  File not found or unsupported type.")
        return
    session = process_audio(path, settings)
    if session and input("\nOpen the report page? (y/n): ").strip().lower() == "y":
        open_report(session)


def action_record(settings):
    seconds = ask_int("Seconds to record [30]: ", 30, 3, 600)
    path = transcribe.record_audio(seconds)
    if path is None:
        return
    name = input("Name for this recording (optional): ").strip()
    session = process_audio(path, settings, name)
    if session and input("\nOpen the report page? (y/n): ").strip().lower() == "y":
        open_report(session)


def action_view():
    session = choose_session()
    if session is None:
        return
    print_session(session)
    if input("\nShow full transcript? (y/n): ").strip().lower() == "y":
        for start, _, text in session["segments"]:
            print(f"  [{analyze.format_time(start)}] {text}")


def action_report():
    """Menu option 4: open the web page report (summary, vocabulary, charts)."""
    session = choose_session()
    if session is not None:
        open_report(session)


def action_export():
    """Menu option 5: save a plain text report."""
    session = choose_session()
    if session is not None:
        print(f"  Text report saved to {storage.export_report(session)}")


def action_settings(settings):
    print("\nCurrent settings:")
    for key, value in settings.items():
        print(f"  {key}: {value}")
    key_status = "set" if ai_summary.get_api_key() else "not set"
    print(f"  AI summary key: {key_status}")
    print("\n1) Whisper model  2) Summary length  3) Number of keywords  4) AI summary key  0) Back")
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
    elif choice == "4":
        key = input("Paste your Anthropic API key (Enter to cancel): ").strip()
        if key:
            ai_summary.save_api_key(key)          # saved in api_key.txt, next to main.py
            print("  Key saved. New and old sessions can now get an AI summary.")


def action_search():
    """Menu option 7: search for a word inside a saved transcript."""
    session = choose_session()          # let the user pick one saved recording from the list
    if session is None:                 # nothing saved, or the user cancelled
        return                          # go back to the menu

    word = input("Word to search for: ").strip()   # ask for the word, .strip() removes extra spaces
    if word == "":                      # the user typed nothing
        print("  Please type a word.")  # tell the user what went wrong
        return                          # go back to the menu

    # ask analyze.py to do the searching in this session's transcript
    matches = analyze.search_transcript(session["segments"], word)

    if len(matches) == 0:               # the list is empty, so nothing was found
        print(f'  No matches for "{word}".')
        return                          # go back to the menu

    print(f'\n{len(matches)} match(es) for "{word}":')   # show how many lines were found
    for start, text in matches:         # go through each result
        # analyze.format_time turns seconds into mm:ss, for example 75 -> 01:15
        print(f"  [{analyze.format_time(start)}] {text}")


def print_menu():
    print("\n===== LectureLens =====")
    print("1) Transcribe an audio file")
    print("2) Record from microphone")
    print("3) View a saved session")
    print("4) Open report page (summary + charts)")
    print("5) Export a text report (.txt)")
    print("6) Settings")
    print("7) Search a transcript")
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
            action_report()
        elif choice == "5":
            action_export()
        elif choice == "6":
            action_settings(settings)
        elif choice == "7":
            action_search()
        elif choice == "0":
            print("Goodbye!")
            break
        else:
            print("  Invalid choice.")


if __name__ == "__main__":
    main()
