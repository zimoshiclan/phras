import pytest

from engine.formality import apply_formality, apply_context, LEVELS, FORBIDDEN_DEFAULTS


SAMPLE_VECTOR = {
    "syntactic": {"f_score": 42.5},
    "lexical": {"contraction_rate": 0.08},
    "corpus_stats": {"avg_words_per_sentence": 11.0},
    "vocabulary": {
        "slang_tokens": ["gonna", "fuck", "lol"],
        "signature_bigrams": ["which means", "makes sense", "anyway so"],
        "top_content_words": ["ship", "build", "team"],
    },
    "emoji_profile": {"emoji_per_100_words": 2.3},
    "function_words": [
        {"word": "which", "z_score": 2.1},
        {"word": "anyway", "z_score": 1.9},
        {"word": "so", "z_score": 1.4},
    ],
}


def test_all_levels_produce_valid_structure():
    for lvl in LEVELS:
        c = apply_formality(SAMPLE_VECTOR, lvl)
        assert c["formality_level"] == lvl
        assert isinstance(c["system_prompt"], str)
        assert len(c["system_prompt"]) > 50
        for forb in FORBIDDEN_DEFAULTS:
            assert forb in c["system_prompt"]


def test_formal_excludes_profanity_and_slang():
    c = apply_formality(SAMPLE_VECTOR, "formal")
    assert "fuck" in c["vocabulary_exclusions"]
    assert c["contraction_policy"] == "none"
    assert c["emoji_policy"] == "none"


def test_no_censor_preserves_slang():
    c = apply_formality(SAMPLE_VECTOR, "no_censor")
    assert c["vocabulary_exclusions"] == []
    assert c["emoji_policy"] == "natural"


def test_semi_formal_reduces_contractions():
    c = apply_formality(SAMPLE_VECTOR, "semi_formal")
    assert c["contraction_policy"] == "reduced"
    assert 50.0 <= c["f_score_target"] <= 60.0


def test_context_appends_email_instruction():
    c = apply_formality(SAMPLE_VECTOR, "semi_formal")
    c2 = apply_context(c, "email")
    assert "email" in c2["system_prompt"].lower()
    assert c2["context"] == "email"


def test_invalid_level_raises():
    with pytest.raises(ValueError):
        apply_formality(SAMPLE_VECTOR, "bogus")
