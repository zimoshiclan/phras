import pytest

pytest.importorskip("nltk")

from engine.extractor import extract_features


SAMPLE = (
    "Honestly, I think maybe this could work out. It's really exciting! "
    "We shipped the thing yesterday, which means we're done for the week. "
    "Anyway, let me know what you think 😄. I've been wondering about the next step."
)


def test_extract_structure():
    out = extract_features(SAMPLE)
    for k in ("corpus_stats", "lexical", "syntactic", "function_words",
              "punctuation", "emoji_profile", "vocabulary"):
        assert k in out
    assert out["corpus_stats"]["word_count"] > 10
    assert 0.0 <= out["syntactic"]["f_score"] <= 100.0
    assert out["lexical"]["contraction_rate"] > 0.0
    assert any(e == "😄" for e in out["emoji_profile"]["unique_emojis"])
    assert isinstance(out["function_words"], list)
    assert out["vocabulary"]["intensifier_ratio"] > 0
