from engine.normalizers import normalize


def test_whatsapp_bracket_and_target_filter():
    raw = (
        "[12/03/23, 10:15:04] Alice: hey there https://example.com\n"
        "[12/03/23, 10:15:08] Bob: <Media omitted>\n"
        "[12/03/23, 10:15:10] Alice: how are you?\n"
        "[12/03/23, 10:15:12] Bob: good thanks\n"
    )
    out = normalize(raw, "whatsapp", target_sender="Alice")
    assert "hey there" in out
    assert "how are you?" in out
    assert "Bob" not in out
    assert "good thanks" not in out
    assert "https://" not in out
    assert "<Media omitted>" not in out


def test_whatsapp_dash_multiline():
    raw = (
        "12/03/2023, 10:15 - Alice: first line\n"
        "continued line\n"
        "12/03/2023, 10:16 - Alice: second msg\n"
    )
    out = normalize(raw, "whatsapp")
    assert "first line continued line" in out
    assert "second msg" in out


def test_telegram_json():
    raw = (
        '{"messages": ['
        '{"type":"message","from":"Alice","text":"hello"},'
        '{"type":"message","from":"Bob","text":"not me"},'
        '{"type":"message","from":"Alice","text":[{"type":"plain","text":"multi "},"part"]}'
        "]}}"
    )
    out = normalize(raw, "telegram", target_sender="Alice")
    assert "hello" in out
    assert "multi part" in out
    assert "not me" not in out


def test_email_strips_headers_and_quotes():
    raw = (
        "From: a@b.com\n"
        "To: c@d.com\n"
        "Subject: hi\n"
        "\n"
        "Hello there, this is my reply.\n"
        "\n"
        "On Mon, Jan 1, 2024 Someone wrote:\n"
        "> original message\n"
    )
    out = normalize(raw, "email")
    assert "Hello there, this is my reply." in out
    assert "original message" not in out
    assert "From:" not in out


def test_twitter_archive():
    raw = (
        'window.YTD.tweet.part0 = [\n'
        '  {"tweet": {"full_text": "just shipped it"}},\n'
        '  {"tweet": {"full_text": "RT @x: not mine"}},\n'
        '  {"tweet": {"full_text": "@alice @bob thanks for the help"}}\n'
        "]"
    )
    out = normalize(raw, "twitter")
    assert "just shipped it" in out
    assert "not mine" not in out
    assert "thanks for the help" in out
    assert "@alice" not in out


def test_essay_strips_page_numbers():
    raw = "Chapter one.\n1\nReal content here.\n42\nMore."
    out = normalize(raw, "essay")
    assert "Chapter one." in out
    assert "Real content here." in out
    assert "More." in out
    lines = out.splitlines()
    assert "1" not in lines and "42" not in lines
