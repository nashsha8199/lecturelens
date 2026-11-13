"""analyze.py - keywords, summary and statistics from an English transcript."""
import re
from collections import Counter

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

from config import ENGLISH_STOPWORDS


def tokenize(text):
    """Split text into lowercase words and remove stopwords and short words."""
    words = re.findall(r"[a-z]+(?:'[a-z]+)?", text.lower())
    # skip contractions such as don't / it's, they carry no topic information
    return [w for w in words
            if "'" not in w and len(w) > 2 and w not in ENGLISH_STOPWORDS]


def word_frequencies(segments):
    """Count every meaningful word. Returns a Counter (dict: word -> count)."""
    counts = Counter()
    for _, _, text in segments:
        counts.update(tokenize(text))
    return counts


def top_keywords(segments, k=10):
    """Rank keywords with TF-IDF (each segment is treated as a small document).

    Returns a list of (word, score) tuples, best first.
    """
    texts = [text for _, _, text in segments]
    if not texts:
        return []
    try:
        vectorizer = TfidfVectorizer(tokenizer=tokenize, lowercase=False, token_pattern=None)
        matrix = vectorizer.fit_transform(texts)
    except ValueError:  # no usable words at all
        return []
    scores = matrix.sum(axis=0).A1
    words = vectorizer.get_feature_names_out()
    ranked = sorted(zip(words, scores), key=lambda pair: pair[1], reverse=True)
    return [(w, round(float(s), 3)) for w, s in ranked[:k]]


def summarize(segments, n=5):
    """Extractive summary: pick the n segments with the most important words."""
    freq = word_frequencies(segments)
    if not freq:
        return []
    biggest = max(freq.values())

    scored = []  # list of (score, original index)
    for i, (_, _, text) in enumerate(segments):
        tokens = tokenize(text)
        if len(tokens) < 3:  # too short to be informative
            continue
        score = sum(freq[t] / biggest for t in tokens) / (len(tokens) ** 0.5)
        scored.append((score, i))

    best = sorted(scored, reverse=True)[:n]
    chosen = sorted(i for _, i in best)  # keep the original order
    return [segments[i][2] for i in chosen]


def pace_table(segments):
    """pandas DataFrame with the number of words spoken in each minute."""
    rows = [{"minute": int(start // 60), "words": len(tokenize(text))}
            for start, _, text in segments]
    if not rows:
        return pd.DataFrame(columns=["minute", "words"])
    df = pd.DataFrame(rows)
    return df.groupby("minute", as_index=False)["words"].sum()


def format_time(seconds):
    """75.3 -> '01:15'"""
    return f"{int(seconds // 60):02d}:{int(seconds % 60):02d}"


def get_stats(result):
    """Basic numbers about the recording, returned as a dict."""
    segments = result["segments"]
    duration = segments[-1][1] if segments else 0
    words = len(result["text"].split())
    return {
        "duration": format_time(duration),
        "segments": len(segments),
        "words": words,
        "words_per_min": round(words / (duration / 60), 1) if duration > 0 else 0,
        "unique_words": len(word_frequencies(segments)),
    }


def search_transcript(segments, query):
    """Find every line of the transcript that contains the word we search for.

    segments = the transcript, a list of (start, end, text) groups
    query    = the word the user typed
    Returns a list of (start, text) pairs, one for each matching line.
    """
    matches = []                       # empty list where we collect the results
    query = query.lower()              # make the word lowercase, so "Model" and "model" are the same

    for start, end, text in segments:  # go through the transcript one line at a time
                                       # (we do not need "end" here, we only use start and text)
        if query in text.lower():      # is the word inside this line? (lowercase, so capitals are ignored)
            matches.append((start, text))   # yes, so save the time and the line

    return matches                     # give the list of results back
