"""ai_summary.py - asks Claude (Anthropic API) to write a real summary of the lecture."""
import json
import os

from config import AI_MODEL, API_KEY_FILE

# The instructions we give to Claude. It must answer in JSON so our program can read it.
INSTRUCTIONS = """You help students study. You get the transcript of a lecture that was made by
speech recognition, so it may contain small mistakes. Fix obvious mistakes silently.
Use ONLY information from the transcript. Write in simple, clear English.

Answer with JSON only, no other text, in exactly this shape:
{
  "tldr": "2-3 sentences that explain what the whole lecture is about",
  "takeaways": ["4 to 6 key points, each one a full sentence, in the order of the lecture"],
  "terms": [{"term": "important word", "definition": "one simple sentence"}],
  "flow": ["3 to 5 main ideas in the order they are explained, 1-4 words each"]
}
Give 5 or 6 items in "terms"."""


def get_api_key():
    """Look for the key in the environment first, then in api_key.txt. Returns "" if none."""
    key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if key:
        return key
    if os.path.isfile(API_KEY_FILE):
        with open(API_KEY_FILE, encoding="utf-8") as f:
            return f.read().strip()
    return ""


def save_api_key(key):
    """Save the key into api_key.txt so the user only has to paste it once."""
    with open(API_KEY_FILE, "w", encoding="utf-8") as f:
        f.write(key.strip())


def parse_reply(raw):
    """Turn Claude's answer (text) into a dict. Returns None if it cannot be read."""
    start = raw.find("{")                 # the JSON starts at the first {
    end = raw.rfind("}")                  # and ends at the last }
    if start == -1 or end == -1:
        return None
    try:
        data = json.loads(raw[start:end + 1])
    except ValueError:
        return None

    terms = []                            # keep only terms that have both a word and a definition
    for item in data.get("terms", []):
        if isinstance(item, dict) and item.get("term") and item.get("definition"):
            terms.append({"term": str(item["term"]), "definition": str(item["definition"])})

    result = {
        "tldr": str(data.get("tldr", "")).strip(),
        "takeaways": [str(p) for p in data.get("takeaways", []) if str(p).strip()],
        "terms": terms,
        "flow": [str(f) for f in data.get("flow", []) if str(f).strip()],
    }
    if result["tldr"] == "":              # no summary at all, so treat it as a failure
        return None
    return result


def ai_summarize(text):
    """Send the transcript to Claude and return the summary dict, or None if it did not work."""
    key = get_api_key()
    if key == "":
        print("  (No API key set, so the simple summary is used. Add one in Settings, option 4.)")
        return None
    try:
        import anthropic
    except ImportError:
        print("  AI summary needs the library: pip3.13 install anthropic")
        return None

    print("  Asking Claude to write the summary...")
    try:
        client = anthropic.Anthropic(api_key=key)
        reply = client.messages.create(
            model=AI_MODEL,
            max_tokens=4000,     # room for the thinking block plus the answer
            system=INSTRUCTIONS,
            messages=[{"role": "user", "content": text[:100000]}],   # limit very long transcripts
        )
        # the reply is a list of blocks; some models add a "thinking" block first,
        # so keep only the blocks of type "text" and join them
        raw = "".join(block.text for block in reply.content if block.type == "text")
    except Exception as error:            # wrong key, no internet, no credit, ...
        print(f"  AI summary failed: {error}")
        return None

    result = parse_reply(raw)
    if result is None:
        print("  Claude's answer could not be read, so the simple summary is used.")
    return result
