"""Stylometric feature extraction — pure-Python + NLTK, no large model files.

Requires NLTK data: averaged_perceptron_tagger_eng (~6 MB, auto-downloaded on
first call). No spaCy or heavy ML models.
Public API: extract_features(text: str) -> dict
"""
from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from typing import Any, NamedTuple

import emoji as emoji_lib

# ── Penn Treebank → Universal POS (UPOS) ───────────────────────────────────────────
_PENN_UPOS: dict[str, str] = {
    "CC": "CCONJ", "CD": "NUM",    "DT": "DET",   "EX": "PRON",
    "FW": "X",     "IN": "ADP",    "JJ": "ADJ",   "JJR": "ADJ",  "JJS": "ADJ",
    "LS": "X",     "MD": "AUX",    "NN": "NOUN",  "NNS": "NOUN",
    "NNP": "PROPN","NNPS": "PROPN","PDT": "DET",  "POS": "PART",
    "PRP": "PRON", "PRP$": "PRON", "RB": "ADV",   "RBR": "ADV",  "RBS": "ADV",
    "RP": "ADP",   "SYM": "SYM",   "TO": "PART",  "UH": "INTJ",
    "VB": "VERB",  "VBD": "VERB",  "VBG": "VERB", "VBN": "VERB", "VBP": "VERB",
    "VBZ": "VERB", "WDT": "DET",   "WP": "PRON",  "WP$": "PRON", "WRB": "ADV",
    ",":  "PUNCT", ".": "PUNCT",   ":": "PUNCT",  "``": "PUNCT", "''": "PUNCT",
    "(":  "PUNCT", ")": "PUNCT",   "$": "SYM",    "#": "SYM",
}

# ── Lightweight token / sentence containers ──────────────────────────────────
@dataclass(slots=True)
class _Tok:
    text: str
    pos: str
    is_alpha: bool


class _Sent(NamedTuple):
    tokens: list[_Tok]
    start_char: int
    end_char: int
    text: str

# ── Regex patterns ────────────────────────────────────────────────────────────────────
_SENT_RE    = re.compile(r'(?<=[.!?\u2026])\s+(?=[A-Z"\u2018\u2019])')
_WORD_RE    = re.compile(r"[a-zA-Z]+")
_ALL_CAPS   = re.compile(r"\b[A-Z]{2,}\b")
_PASSIVE_RE = re.compile(
    r"\b(?:am|is|are|was|were|be|been|being)\s+\w+(?:ed|en|wn)\b",
    re.IGNORECASE,
)
_CONTRACTION_RE = re.compile(
    r"\b\w+(?:'s|'re|'ve|'ll|'d|'m|n't|'em)\b", re.IGNORECASE,
)

# ── Embedded lexical sets (no corpus download needed) ───────────────────────────
_STOPWORDS = frozenset({
    "i","me","my","myself","we","our","ours","ourselves",
    "you","your","yours","yourself","yourselves",
    "he","him","his","himself","she","her","hers","herself",
    "it","its","itself","they","them","their","theirs","themselves",
    "what","which","who","whom","this","that","these","those",
    "am","is","are","was","were","be","been","being",
    "have","has","had","having","do","does","did","doing",
    "will","would","shall","should","may","might","must","can","could",
    "a","an","the","and","but","if","or","because","as","until",
    "while","of","at","by","for","with","about","against","between",
    "into","through","during","before","after","above","below",
    "to","from","up","down","in","out","on","off","over","under",
    "again","further","then","once","here","there","when","where",
    "why","how","all","both","each","few","more","most","other",
    "some","such","no","not","only","own","same","so","than",
    "too","very","just","now","s","t","d","ll","m","re","ve",
    "don","ain","aren","couldn","didn","doesn","hadn","hasn",
    "haven","isn","mightn","mustn","needn","shan","shouldn",
    "wasn","weren","won","wouldn",
})

_SCONJ = frozenset({
    "because","although","though","unless","when","while","after","before",
    "since","if","whether","whereas","until","once","as","that","which",
    "who","whom",
})

_HEDGE_WORDS = frozenset({
    "maybe","perhaps","probably","possibly","somewhat","sort","kind",
    "might","could","arguably","roughly","approximately","seemingly",
})
_INTENSIFIERS = frozenset({
    "very","so","really","absolutely","totally","extremely","incredibly",
    "super","highly","utterly","completely","deeply","insanely",
})

# ── Baseline function-word frequencies per 1000 tokens (Brown corpus norms)
# Source: Mosteller & Wallace-style baselines; z-scores reveal per-user
# deviations that fingerprint writing voice.
_FUNCTION_WORD_BASELINE_PER_1000: dict[str, float] = {
    "the": 69.97, "of": 36.41, "and": 28.85, "to": 26.76, "a": 23.25,
    "in": 21.34, "that": 10.99, "is": 10.10, "was": 9.82, "for": 9.34,
    "it": 8.77, "with": 7.79, "as": 7.24, "be": 6.39, "on": 6.73,
    "by": 5.40, "at": 5.23, "this": 5.11, "are": 4.67, "from": 4.54,
    "or": 4.28, "have": 4.00, "an": 3.77, "they": 3.59, "but": 3.42,
    "not": 4.13, "which": 3.78, "he": 9.64, "she": 2.86, "we": 2.73,
    "his": 6.99, "her": 3.06, "their": 2.80, "its": 1.94, "one": 2.94,
    "all": 3.34, "would": 2.71, "there": 2.35, "will": 2.64, "been": 2.47,
    "had": 5.07, "has": 2.63, "were": 3.24, "when": 2.33, "so": 1.82,
    "up": 2.48, "out": 2.96, "if": 2.52, "about": 1.74, "what": 2.17,
    "can": 2.30, "my": 2.00, "your": 2.20, "no": 2.05, "me": 1.44,
    "you": 6.20, "i": 5.50, "do": 1.81, "who": 2.55, "some": 2.12,
}

# ── NLTK lazy loader ─────────────────────────────────────────────────────────────
_NLTK_READY = False


def _ensure_nltk() -> None:
    global _NLTK_READY
    if _NLTK_READY:
        return
    try:
        import nltk
        nltk.download("averaged_perceptron_tagger_eng", quiet=True)
    except Exception:
        pass
    _NLTK_READY = True


def _parse(text: str) -> tuple[list[_Tok], list[_Sent]]:
    _ensure_nltk()
    import nltk

    raw_sents = _SENT_RE.split(text) or [text]
    all_toks: list[_Tok] = []
    sentences: list[_Sent] = []
    cursor = 0

    for sent_text in raw_sents:
        start = text.find(sent_text, cursor)
        if start == -1:
            start = cursor
        end = start + len(sent_text)
        cursor = end

        words = _WORD_RE.findall(sent_text)
        if not words:
            continue

        try:
            tagged = nltk.pos_tag(words)
        except LookupError:
            tagged = [(w, "NN") for w in words]

        sent_toks = [
            _Tok(text=w, pos=_PENN_UPOS.get(tag, "X"), is_alpha=True)
            for w, tag in tagged
        ]
        all_toks.extend(sent_toks)
        sentences.append(_Sent(tokens=sent_toks, start_char=start, end_char=end, text=sent_text))

    return all_toks, sentences


# ── Public API ─────────────────────────────────────────────────────────────────────────────

def extract_features(text: str) -> dict[str, Any]:
    if not text or not text.strip():
        raise ValueError("empty text")
    tokens, sentences = _parse(text)
    words = [t for t in tokens if t.is_alpha]

    return {
        "corpus_stats":   _corpus_stats(text, words, sentences),
        "lexical":        _lexical(words, text),
        "syntactic":      _syntactic(tokens, sentences),
        "function_words": _function_words(words),
        "punctuation":    _punctuation(text, tokens, sentences),
        "emoji_profile":  _emoji_profile(text, words, sentences),
        "vocabulary":     _vocabulary(words),
    }


# ── Section implementations ────────────────────────────────────────────────────────────────

def _corpus_stats(text: str, words: list[_Tok], sentences: list[_Sent]) -> dict:
    sent_lengths = [len(s.tokens) for s in sentences if s.tokens]
    return {
        "word_count":              len(words),
        "sentence_count":          len(sentences),
        "char_count":              len(text),
        "avg_words_per_sentence":  _mean(sent_lengths),
        "median_sentence_length":  _median(sent_lengths),
    }


def _lexical(words: list[_Tok], text: str) -> dict:
    lowered = [w.text.lower() for w in words]
    n = len(lowered)
    freq = Counter(lowered)
    unique = len(freq)
    hapax = sum(1 for c in freq.values() if c == 1)
    yules_k = 10_000 * (sum(c * c for c in freq.values()) - n) / (n * n) if n else 0.0

    lens = [len(w) for w in lowered]
    buckets: dict[str, int] = {}
    for L in lens:
        key = str(L) if L < 10 else "10+"
        buckets[key] = buckets.get(key, 0) + 1
    dist = {k: v / n if n else 0.0
            for k, v in sorted(buckets.items(), key=_bucket_sort)}

    return {
        "type_token_ratio":       (unique / n) if n else 0.0,
        "yules_k":                yules_k,
        "hapax_legomena_ratio":   (hapax / unique) if unique else 0.0,
        "avg_word_length":        _mean(lens),
        "word_length_distribution": dist,
        "contraction_rate":       len(_CONTRACTION_RE.findall(text)) / n if n else 0.0,
    }


def _bucket_sort(kv: tuple[str, int]) -> tuple[int, str]:
    k = kv[0]
    return (10 if k == "10+" else int(k), k)


def _syntactic(tokens: list[_Tok], sentences: list[_Sent]) -> dict:
    total = len(tokens) or 1
    pos_counts = Counter(t.pos for t in tokens)

    def freq(pos: str) -> float:
        return (pos_counts.get(pos, 0) / total) * 100

    noun_f = freq("NOUN") + freq("PROPN")
    adj_f  = freq("ADJ")
    prep_f = freq("ADP")
    det_f  = freq("DET")
    pron_f = freq("PRON")
    verb_f = freq("VERB") + freq("AUX")
    adv_f  = freq("ADV")
    intj_f = freq("INTJ")
    f_score = (noun_f + adj_f + prep_f + det_f - pron_f - verb_f - adv_f - intj_f + 100) / 2

    sent_total  = len(sentences) or 1
    passive     = sum(1 for s in sentences if _PASSIVE_RE.search(s.text))
    subordinate = sum(1 for s in sentences
                      if any(t.text.lower() in _SCONJ for t in s.tokens))

    opener_pos: Counter[str] = Counter()
    for s in sentences:
        first = next((t for t in s.tokens), None)
        if first:
            opener_pos[first.pos] += 1
    opener_dist = {k: v / sent_total for k, v in opener_pos.items()}

    pronouns = [t for t in tokens if t.pos == "PRON"]
    n_pron   = len(pronouns) or 1
    fp1 = {"i", "me", "my", "mine", "myself"}
    fp2 = {"you", "your", "yours", "yourself", "yourselves"}

    return {
        "f_score":                     f_score,
        "passive_voice_ratio":         passive / sent_total,
        "subordinate_clause_ratio":    subordinate / sent_total,
        "sentence_opener_distribution": opener_dist,
        "pronoun_ratio":               pron_f / 100,
        "noun_ratio":                  noun_f / 100,
        "verb_ratio":                  verb_f / 100,
        "adjective_ratio":             adj_f / 100,
        "adverb_ratio":                adv_f / 100,
        "first_person_ratio":          sum(1 for t in pronouns if t.text.lower() in fp1) / n_pron,
        "second_person_ratio":         sum(1 for t in pronouns if t.text.lower() in fp2) / n_pron,
        "question_sentence_ratio":     sum(1 for s in sentences if s.text.rstrip().endswith("?")) / sent_total,
    }


def _function_words(words: list[_Tok]) -> list[dict]:
    n = len(words)
    if n == 0:
        return []
    freq = Counter(w.text.lower() for w in words)
    results: list[dict] = []
    for fw, baseline in _FUNCTION_WORD_BASELINE_PER_1000.items():
        per_1k = (freq.get(fw, 0) / n) * 1000
        sd = math.sqrt(baseline) if baseline > 0 else 1.0
        results.append({
            "word":          fw,
            "freq_per_1000": round(per_1k, 3),
            "z_score":       round((per_1k - baseline) / sd, 3),
        })
    results.sort(key=lambda r: abs(r["z_score"]), reverse=True)
    return results


def _punctuation(text: str, tokens: list[_Tok], sentences: list[_Sent]) -> dict:
    n_words = sum(1 for t in tokens if t.is_alpha) or 1
    n_sent  = len(sentences) or 1
    per_100 = lambda c: (c / n_words) * 100
    return {
        "exclamation_per_100": per_100(text.count("!")),
        "question_per_100":    per_100(text.count("?")),
        "ellipsis_per_100":    per_100(text.count("...") + text.count("\u2026")),
        "semicolon_per_100":   per_100(text.count(";")),
        "dash_per_100":        per_100(text.count("\u2014") + text.count(" - ")),
        "comma_per_sentence":  text.count(",") / n_sent,
        "all_caps_word_ratio": len(_ALL_CAPS.findall(text)) / n_words,
    }


def _emoji_profile(text: str, words: list[_Tok], sentences: list[_Sent]) -> dict:
    found   = emoji_lib.emoji_list(text)
    n_words = len(words) or 1
    if not found:
        return {
            "emoji_per_100_words": 0.0,
            "unique_emojis": [],
            "position_distribution": {
                "sentence_start": 0.0, "sentence_middle": 0.0, "sentence_end": 0.0,
            },
            "top_5_emojis": [],
        }
    counts = Counter(e["emoji"] for e in found)
    starts = mids = ends = 0
    for e in found:
        idx = e["match_start"]
        for s in sentences:
            if s.start_char <= idx < s.end_char:
                rel    = idx - s.start_char
                length = s.end_char - s.start_char or 1
                if rel < length * 0.2:
                    starts += 1
                elif rel > length * 0.8:
                    ends   += 1
                else:
                    mids   += 1
                break
    total = len(found) or 1
    return {
        "emoji_per_100_words": (total / n_words) * 100,
        "unique_emojis":       sorted(counts.keys()),
        "position_distribution": {
            "sentence_start":  starts / total,
            "sentence_middle": mids   / total,
            "sentence_end":    ends   / total,
        },
        "top_5_emojis": [e for e, _ in counts.most_common(5)],
    }


_ENGLISH_WORDS_CACHE: set[str] | None = None


def _english_words() -> set[str]:
    global _ENGLISH_WORDS_CACHE
    if _ENGLISH_WORDS_CACHE is None:
        try:
            from nltk.corpus import words as _w
            _ENGLISH_WORDS_CACHE = {w.lower() for w in _w.words()}
        except (ImportError, LookupError):
            _ENGLISH_WORDS_CACHE = set()
    return _ENGLISH_WORDS_CACHE


def _vocabulary(words: list[_Tok]) -> dict:
    lowered = [w.text.lower() for w in words]
    content = [w for w in lowered if w not in _STOPWORDS]
    top_content = [w for w, _ in Counter(content).most_common(30)]

    bigrams  = Counter(zip(lowered, lowered[1:]))
    trigrams = Counter(zip(lowered, lowered[1:], lowered[2:]))

    def distinctive_ngrams(cnt: Counter, k: int, min_count: int) -> list[str]:
        items = sorted(
            [(ng, c) for ng, c in cnt.items()
             if c >= min_count and any(tok not in _STOPWORDS for tok in ng)],
            key=lambda x: x[1], reverse=True,
        )
        return [" ".join(ng) for ng, _ in items[:k]]

    total   = len(lowered) or 1
    english = _english_words()
    slang   = [w for w in set(lowered)
               if english and w not in english and w.isalpha() and len(w) > 2]

    return {
        "top_content_words":   top_content,
        "signature_bigrams":   distinctive_ngrams(bigrams,  15, min_count=2),
        "signature_trigrams":  distinctive_ngrams(trigrams, 10, min_count=2),
        "hedging_word_ratio":  sum(1 for w in lowered if w in _HEDGE_WORDS) / total,
        "intensifier_ratio":   sum(1 for w in lowered if w in _INTENSIFIERS) / total,
        "slang_tokens":        slang[:50],
    }


# ── Helpers ───────────────────────────────────────────────────────────────────────────────

def _mean(xs: list) -> float:
    return float(sum(xs) / len(xs)) if xs else 0.0


def _median(xs: list) -> float:
    if not xs:
        return 0.0
    s   = sorted(xs)
    n   = len(s)
    mid = n // 2
    return float(s[mid]) if n % 2 else (s[mid - 1] + s[mid]) / 2.0
