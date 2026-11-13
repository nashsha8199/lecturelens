"""visualize.py - charts for one session."""
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud

import analyze


def show_dashboard(session):
    """Word cloud + keyword bar chart + speaking pace, in one window."""
    segments = [tuple(s) for s in session["segments"]]
    freq = analyze.word_frequencies(segments)
    if not freq:
        print("  Not enough words to draw charts.")
        return

    fig, axes = plt.subplot_mosaic([["cloud", "cloud"], ["kw", "pace"]], figsize=(12, 8))

    # 1) word cloud
    cloud = WordCloud(width=1000, height=350, background_color="white") \
        .generate_from_frequencies(dict(freq))
    axes["cloud"].imshow(cloud, interpolation="bilinear")
    axes["cloud"].axis("off")
    axes["cloud"].set_title(f"Word cloud - {session['name']}")

    # 2) top keywords (TF-IDF)
    keywords = session["keywords"]
    if keywords:
        words = [w for w, _ in keywords]
        scores = [s for _, s in keywords]
        sns.barplot(x=scores, y=words, color="tab:orange", ax=axes["kw"])
    axes["kw"].set_title("Top keywords (TF-IDF)")
    axes["kw"].set_xlabel("score")

    # 3) words spoken per minute
    pace = analyze.pace_table(segments)
    if not pace.empty:
        sns.barplot(data=pace, x="minute", y="words", color="tab:blue", ax=axes["pace"])
    axes["pace"].set_title("Speaking pace")
    axes["pace"].set_xlabel("minute")
    axes["pace"].set_ylabel("words")

    plt.tight_layout()
    plt.show()
