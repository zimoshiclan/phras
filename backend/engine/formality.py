"""Formality multiplier.

Public API: `apply_formality(style_vector: dict, level: str) -> dict`
Produces a constraint object including a ready-to-inject `system_prompt`.
"""
from __future__ import annotations

from typing import Any

LEVELS = {"no_censor", "casual", "family", "semi_formal", "formal"}

FORBIDDEN_DEFAULTS = [
    "Certainly!",
    "Great question!",
    "I hope this email finds you well",
    "As an AI language model",
    "I'd be happy to",
]

_PROFANITY = {
    "fuck", "fucking", "shit", "shitty", "bitch", "ass", "asshole",
    "bastard", "damn", "dick", "piss", "cunt",
}


def apply_formality(style_vector: dict[str, Any], level: str) -> dict[str, Any]:
    if level not in LEVELS:
        raise ValueError(f"invalid level: {level!r}")

    syn = style_vector.get("syntactic", {})
    lex = style_vector.get("lexical", {})
    vocab = style_vector.get("vocabulary", {})
    emo = style_vector.get("emoji_profile", {})
    corpus = style_vector.get("corpus_stats", {})
    fwords = style_vector.get("function_words", [])

    user_f = float(syn.get("f_score", 50.0))
    user_contraction = float(lex.get("contraction_rate", 0.0))
    user_avg_sent = float(corpus.get("avg_words_per_sentence", 14.0))
    slang = list(vocab.get("slang_tokens", []))
    bigrams = list(vocab.get("signature_bigrams", []))[:10]
    top_content = list(vocab.get("top_content_words", []))[:10]
    top_fw = [fw["word"] for fw in fwords[:5]] if fwords else []

    def _non_profane(words: list[str]) -> list[str]:
        return [w for w in words if w.lower() not in _PROFANITY]

    if level == "no_censor":
        c = {
            "f_score_target": user_f,
            "sentence_length_target": f"{max(1, int(user_avg_sent - 1))}\u2013{int(user_avg_sent + 1)} words",
            "contraction_policy": "allowed",
            "emoji_policy": "natural",
            "pronoun_guidance": "use first person freely",
            "vocabulary_inclusions": bigrams + top_content,
            "vocabulary_exclusions": [],
            "signature_phrases": bigrams[:5],
            "forbidden_patterns": list(FORBIDDEN_DEFAULTS),
            "opening_style": "direct \u2014 start with the point",
        }
    elif level == "casual":
        target_f = user_f if user_f < 50 else user_f - 8
        c = {
            "f_score_target": target_f,
            "sentence_length_target": f"{max(1, int(user_avg_sent - 2))}\u2013{int(user_avg_sent + 2)} words",
            "contraction_policy": "allowed",
            "emoji_policy": "natural",
            "pronoun_guidance": "first person singular is fine",
            "vocabulary_inclusions": _non_profane(bigrams + top_content),
            "vocabulary_exclusions": [w for w in slang if w.lower() in _PROFANITY],
            "signature_phrases": _non_profane(bigrams)[:5],
            "forbidden_patterns": list(FORBIDDEN_DEFAULTS),
            "opening_style": "conversational opener",
        }
    elif level == "family":
        c = {
            "f_score_target": user_f if user_f < 50 else user_f - 8,
            "sentence_length_target": f"{max(1, int(user_avg_sent - 3))}\u2013{int(user_avg_sent + 1)} words",
            "contraction_policy": "allowed",
            "emoji_policy": "natural",
            "pronoun_guidance": "use inclusive language (we, us, together) where natural",
            "vocabulary_inclusions": _non_profane(bigrams + top_content),
            "vocabulary_exclusions": list(_PROFANITY) + [w for w in slang if w.lower() in _PROFANITY],
            "signature_phrases": _non_profane(bigrams)[:5],
            "forbidden_patterns": list(FORBIDDEN_DEFAULTS),
            "opening_style": "warm, inclusive",
        }
    elif level == "semi_formal":
        c = {
            "f_score_target": max(50.0, min(60.0, user_f)),
            "sentence_length_target": "12\u201315 words",
            "contraction_policy": "reduced",
            "emoji_policy": "max_1_end",
            "pronoun_guidance": "first person acceptable; avoid slang forms",
            "vocabulary_inclusions": _non_profane(bigrams),
            "vocabulary_exclusions": list(slang) + list(_PROFANITY),
            "signature_phrases": _non_profane(bigrams)[:5],
            "forbidden_patterns": list(FORBIDDEN_DEFAULTS),
            "opening_style": "direct, professional",
            "preserve_function_words": top_fw,
        }
    else:  # formal
        c = {
            "f_score_target": max(65.0, min(80.0, user_f + 15)),
            "sentence_length_target": "15\u201320 words",
            "contraction_policy": "none",
            "emoji_policy": "none",
            "pronoun_guidance": "minimize first person singular; prefer passive/impersonal constructions",
            "vocabulary_inclusions": _non_profane(bigrams)[:3],
            "vocabulary_exclusions": list(slang) + list(_PROFANITY),
            "signature_phrases": _non_profane(bigrams)[:3],
            "forbidden_patterns": list(FORBIDDEN_DEFAULTS),
            "opening_style": "formal, impersonal",
            "preserve_function_words": top_fw[:3],
        }

    c["formality_level"] = level
    c["system_prompt"] = _system_prompt(level, c)
    return c


def _system_prompt(level: str, c: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append(
        f"Write in direct sentences averaging {c['sentence_length_target']}. "
        f"Target formality score ~{int(round(c['f_score_target']))}/100."
    )

    if c["contraction_policy"] == "allowed":
        lines.append("Use contractions naturally (don't, won't, it's).")
    elif c["contraction_policy"] == "reduced":
        lines.append("Use contractions sparingly \u2014 mostly the common ones only.")
    else:
        lines.append("Do not use contractions.")

    sigs = c.get("signature_phrases") or []
    if sigs:
        preview = ", ".join(f"'{p}'" for p in sigs[:5])
        lines.append(f"These phrases appear naturally in this person's writing \u2014 use them where they fit: {preview}.")

    excl = c.get("vocabulary_exclusions") or []
    if excl:
        lines.append(f"Avoid these words/registers: {', '.join(excl[:8])}.")

    forbid = ", ".join(f"'{p}'" for p in c["forbidden_patterns"])
    lines.append(f"Never open with or include: {forbid}.")

    if c["emoji_policy"] == "natural":
        lines.append("Emoji: use them at the user's natural rate \u2014 don't force them, don't suppress them.")
    elif c["emoji_policy"] == "max_1_end":
        lines.append("Emoji: at most one, only at the end if warranted.")
    else:
        lines.append("Do not use emoji.")

    lines.append(f"Opening style: {c['opening_style']}.")
    lines.append(f"Pronouns: {c['pronoun_guidance']}.")

    if level == "formal":
        lines.append("Close with a formal sign-off derived from the user's corpus if one exists; otherwise use 'Regards'.")
    elif level == "semi_formal":
        lines.append("Close with a short sign-off \u2014 not 'Best regards'.")

    return " ".join(lines)


def apply_context(constraint: dict[str, Any], context: str | None) -> dict[str, Any]:
    if not context:
        return constraint
    addenda = {
        "email": "This is an email. Include a subject line suggestion. Use an appropriate sign-off.",
        "reply": "This is a reply. Be responsive to what was said. Match the incoming energy.",
        "tweet": "This is a tweet. Max 280 characters. No sign-off.",
        "linkedin": "This is a LinkedIn post. Professional but personal. No excessive hashtags.",
        "general": "",
    }
    add = addenda.get(context, "")
    if add:
        out = dict(constraint)
        out["system_prompt"] = constraint["system_prompt"] + " " + add
        out["context"] = context
        return out
    out = dict(constraint)
    out["context"] = context
    return out
