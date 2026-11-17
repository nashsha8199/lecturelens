"""visualize.py - draws the two charts for the report page (as images)."""
import base64
import io

import matplotlib
matplotlib.use("Agg")                      # draw into memory, no chart window needed
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import seaborn as sns

import analyze

COLOR = "#6366f1"                          # indigo, matches the report page


def figure_to_base64(fig):
    """Turn a finished chart into text, so it can sit inside the HTML page."""
    buffer = io.BytesIO()                  # a file that lives in memory
    fig.savefig(buffer, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def keyword_chart(keywords):
    """Horizontal bars: the top keywords (TF-IDF score)."""
    fig, ax = plt.subplots(figsize=(6, 4.2))
    words = [w for w, _ in keywords]       # split the (word, score) tuples into two lists
    scores = [s for _, s in keywords]
    sns.barplot(x=scores, y=words, color=COLOR, ax=ax)
    ax.set_title("Top keywords", loc="left", fontweight="bold")
    ax.set_xlabel("TF-IDF score")
    sns.despine(ax=ax)                     # remove the top and right lines
    return figure_to_base64(fig)


def pace_chart(segments):
    """Bars: how many words were spoken in each minute."""
    pace = analyze.pace_table(segments)    # pandas table with the columns minute, words
    fig, ax = plt.subplots(figsize=(6, 4.2))
    ax.bar(pace["minute"], pace["words"], color="#94a3b8")
    ax.set_title("Speaking pace", loc="left", fontweight="bold")
    ax.set_xlabel("minute")
    ax.set_ylabel("words")
    ax.xaxis.set_major_locator(MaxNLocator(integer=True, nbins=12))   # keep minute labels readable
    sns.despine(ax=ax)
    return figure_to_base64(fig)


def make_charts(session):
    """Return (keyword chart, pace chart) as base64 text. An empty string means 'no chart'."""
    segments = [tuple(s) for s in session["segments"]]   # JSON turns tuples into lists, convert back
    keyword_img = keyword_chart(session["keywords"]) if session["keywords"] else ""
    pace_img = pace_chart(segments) if segments else ""
    return keyword_img, pace_img
