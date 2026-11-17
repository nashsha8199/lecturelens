"""report.py - builds the web page report (summary, vocabulary, flow and charts)."""
import html
import os

import analyze
import visualize
from config import SESSIONS_DIR, GLOSSARY

# The look of the page (plain CSS, nothing to install)
CSS = """
body{margin:0;background:#f8fafc;color:#0f172a;font:15px/1.6 -apple-system,Segoe UI,Arial,sans-serif}
.wrap{max-width:900px;margin:0 auto;padding:32px 20px}
h1{margin:0 0 6px;font-size:30px;letter-spacing:-.02em}
.meta{color:#64748b;font-size:13px;margin-bottom:6px}
.topic{color:#4f46e5;font-weight:600;margin-bottom:22px}
.card{background:#fff;border:1px solid #e2e8f0;border-radius:12px;box-shadow:0 1px 2px rgba(0,0,0,.05);padding:20px;margin-bottom:18px}
.tldr{background:#eef2ff;border-color:#c7d2fe;font-size:16.5px}
h2{margin:0 0 12px;font-size:13px;letter-spacing:.06em;text-transform:uppercase;color:#4f46e5}
ul{margin:0;padding-left:20px} li{margin-bottom:6px}
dt{font-weight:600} dd{margin:2px 0 12px;color:#475569}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:18px}
.flow{display:flex;flex-wrap:wrap;align-items:center;gap:8px}
.step{background:#eef2ff;border:1px solid #c7d2fe;color:#3730a3;border-radius:10px;padding:8px 14px;font-weight:600}
.arrow{color:#94a3b8;font-size:20px}
.charts{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.charts img{width:100%}
.note{color:#64748b;font-size:13px}
@media(max-width:700px){.grid,.charts{grid-template-columns:1fr}}
"""


def clean_title(name):
    """Make a readable title: 'intro_to-ML' -> 'Intro To Ml'."""
    return name.replace("_", " ").replace("-", " ").strip().title()


def find_sentence(segments, word):
    """Return the first transcript line that contains the word (or '' if none)."""
    for _, _, text in segments:           # go through the transcript line by line
        if word in text.lower():
            return text
    return ""


def fallback_vocabulary(session):
    """Vocabulary without AI: GLOSSARY definition if we have one, else a sentence from the lecture."""
    items = []
    for word, _ in session["keywords"][:6]:
        if word in GLOSSARY:
            items.append((word.title(), GLOSSARY[word]))
        else:
            sentence = find_sentence(session["segments"], word)
            if sentence:
                items.append((word.title(), 'In the lecture: "' + sentence + '"'))
    return items


def get_content(session):
    """Collect what the page shows: from the AI summary if there is one, otherwise the simple summary."""
    ai = session.get("ai")
    if ai:
        return {
            "tldr": ai["tldr"],
            "takeaways": ai["takeaways"],
            "vocab": [(t["term"], t["definition"]) for t in ai["terms"]],
            "flow": ai["flow"],
            "is_ai": True,
        }
    return {
        "tldr": " ".join(analyze.summarize(session["segments"], 2)),
        "takeaways": session["summary"],
        "vocab": fallback_vocabulary(session),
        "flow": [],
        "is_ai": False,
    }


def export_html(session):
    """Write the web page report into the sessions folder. Returns its path."""
    os.makedirs(SESSIONS_DIR, exist_ok=True)
    path = os.path.join(SESSIONS_DIR, f"{session['id']}_report.html")
    content = get_content(session)
    stats = session["stats"]
    title = html.escape(clean_title(session["name"]))
    topic = " &middot; ".join(html.escape(w) for w, _ in session["keywords"][:3])

    takeaways = "".join(f"<li>{html.escape(t)}</li>" for t in content["takeaways"])
    vocab = "".join(f"<dt>{html.escape(w)}</dt><dd>{html.escape(d)}</dd>" for w, d in content["vocab"])

    flow_card = ""                            # the flow card only exists when we have a flow
    if content["flow"]:
        steps = '<span class="arrow">&rarr;</span>'.join(
            f'<span class="step">{html.escape(step)}</span>' for step in content["flow"])
        flow_card = f'<div class="card"><h2>Concept flow</h2><div class="flow">{steps}</div></div>'

    keyword_img, pace_img = visualize.make_charts(session)
    charts = ""
    for image in (keyword_img, pace_img):
        if image:
            charts += f'<img src="data:image/png;base64,{image}" alt="chart">'

    note = ""
    if not content["is_ai"]:
        note = ('<div class="note">Simple summary: sentences picked from the lecture. '
                'Add an API key in Settings for an AI-written summary.</div>')

    page = f"""<!doctype html><html><head><meta charset="utf-8">
<title>{title}</title><style>{CSS}</style></head><body><div class="wrap">
<h1>{title}</h1>
<div class="meta">{session['created']} &middot; {stats['duration']} &middot; {stats['words']} words &middot; {stats['words_per_min']} words/min</div>
<div class="topic">Topic: {topic}</div>
<div class="card tldr"><h2>TL;DR</h2>{html.escape(content['tldr'])}{note}</div>
<div class="grid">
<div class="card"><h2>Key takeaways</h2><ul>{takeaways}</ul></div>
<div class="card"><h2>Vocabulary</h2><dl>{vocab}</dl></div>
</div>
{flow_card}
<div class="card"><h2>Charts</h2><div class="charts">{charts}</div></div>
</div></body></html>"""

    with open(path, "w", encoding="utf-8") as f:
        f.write(page)
    return path
