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


def split_sentences(segments):
    """Join the transcript pieces, then cut the text into real sentences.

    Whisper pieces often stop in the middle of a sentence,
    so we must join them first and split at . ! ? instead.
    """
    full_text = " ".join(text for _, _, text in segments)    # one long string
    pieces = re.split(r"(?<=[.!?])\s+", full_text)           # cut after . ! or ?
    return [p.strip() for p in pieces if p.strip()]          # drop empty pieces


def tidy(sentence):
    """Remove a spoken starter like 'So,' or 'And' and make the first letter a capital."""
    sentence = re.sub(r"^(so|and|but|now|okay|alright|well)\b,?\s+", "", sentence, flags=re.I)
    return sentence[:1].upper() + sentence[1:]


def summarize(segments, n=5):
    """Extractive summary: the best sentence from each of n parts of the lecture."""
    freq = word_frequencies(segments)         # how often each important word is said
    if not freq:
        return []
    biggest = max(freq.values())
    sentences = split_sentences(segments)

    scored = []                               # list of (score, sentence number)
    for i, sentence in enumerate(sentences):
        tokens = tokenize(sentence)
        word_count = len(sentence.split())
        # skip sentences that are too short or too long to read well
        if len(tokens) < 3 or word_count < 6 or word_count > 40:
            continue
        # skip spoken transitions such as "Let's move on" or "Thank you for watching"
        if re.match(r"^(so |now |okay )?(let's|let us|thank|welcome|today we|in this video)", sentence, flags=re.I):
            continue
        # unique important words, common words score higher; divide by length so long sentences do not always win
        score = sum(freq[t] / biggest for t in set(tokens)) / (len(tokens) ** 0.5)
        scored.append((score, i))

    # cut the lecture into n equal parts and take the best sentence of each part,
    # so the summary covers the whole lecture and not just one topic
    chosen = []
    size = len(sentences) / n
    for part in range(n):
        in_part = [(score, i) for score, i in scored
                   if part * size <= i < (part + 1) * size]
        if in_part:
            chosen.append(max(in_part)[1])    # max picks the highest score

    return [tidy(sentences[i]) for i in sorted(chosen)]   # keep the lecture order


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
