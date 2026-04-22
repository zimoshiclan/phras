"""Per-source text normalizers.

Public API: `normalize(raw_text, source, target_sender=None) -> str`
Returns a single clean UTF-8 string containing only the target user's words.
"""
from __future__ import annotations

import csv
import io
import json
import re
from html.parser import HTMLParser
from typing import Optional

URL_RE = re.compile(r"https?://\S+")
MULTI_WS_RE = re.compile(r"[ \t]+")
MULTI_NL_RE = re.compile(r"\n{3,}")

_SUPPORTED = {"whatsapp", "telegram", "email", "twitter", "linkedin", "essay", "plain"}


def normalize(raw_text: str, source: str, target_sender: Optional[str] = None) -> str:
    if source not in _SUPPORTED:
        raise ValueError(f"unsupported source: {source!r}")
    fn = _DISPATCH[source]
    out = fn(raw_text, target_sender)
    return _tidy(out)


def _tidy(text: str) -> str:
    text = URL_RE.sub("", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = MULTI_WS_RE.sub(" ", text)
    text = MULTI_NL_RE.sub("\n\n", text)
    return text.strip()


# ---------- WhatsApp ----------

# [DD/MM/YY, HH:MM:SS] Name:   |  DD/MM/YYYY, HH:MM - Name:
_WA_BRACKET = re.compile(
    r"^\[(\d{1,2}/\d{1,2}/\d{2,4}),\s+(\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM|am|pm)?)\]\s+([^:]+?):\s?(.*)$"
)
_WA_DASH = re.compile(
    r"^(\d{1,2}/\d{1,2}/\d{2,4}),\s+(\d{1,2}:\d{2}(?:\s*(?:AM|PM|am|pm))?)\s+-\s+([^:]+?):\s?(.*)$"
)
_WA_SYSTEM = re.compile(
    r"(<Media omitted>|This message was deleted|You deleted this message|Missed voice call|Missed video call|image omitted|video omitted|audio omitted|sticker omitted|GIF omitted|Contact card omitted|Messages and calls are end-to-end encrypted)",
    re.IGNORECASE,
)


def _norm_whatsapp(text: str, target_sender: Optional[str]) -> str:
    lines = text.splitlines()
    collected: list[str] = []
    current_sender: Optional[str] = None
    current_buf: list[str] = []

    def flush():
        nonlocal current_sender, current_buf
        if current_sender is not None and current_buf:
            msg = " ".join(current_buf).strip()
            if msg and not _WA_SYSTEM.search(msg):
                if target_sender is None or current_sender.strip() == target_sender.strip():
                    collected.append(msg)
        current_buf = []

    for ln in lines:
        m = _WA_BRACKET.match(ln) or _WA_DASH.match(ln)
        if m:
            flush()
            current_sender = m.group(3)
            current_buf = [m.group(4)]
        else:
            if current_sender is not None:
                current_buf.append(ln)
    flush()
    return "\n".join(collected)


# ---------- Telegram ----------


def _norm_telegram(text: str, target_sender: Optional[str]) -> str:
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return ""
    messages = data.get("messages", []) if isinstance(data, dict) else []
    out: list[str] = []
    for m in messages:
        if not isinstance(m, dict):
            continue
        if m.get("type") != "message":
            continue
        sender = m.get("from") or ""
        if target_sender and sender.strip() != target_sender.strip():
            continue
        txt = m.get("text", "")
        if isinstance(txt, list):
            parts = []
            for p in txt:
                if isinstance(p, str):
                    parts.append(p)
                elif isinstance(p, dict):
                    parts.append(p.get("text", ""))
            flat = "".join(parts)
        else:
            flat = str(txt)
        flat = flat.strip()
        if flat:
            out.append(flat)
    return "\n".join(out)


# ---------- Email ----------

_EMAIL_HEADER_RE = re.compile(
    r"^(From|To|Subject|Date|Cc|Bcc|Sent|Reply-To|Return-Path|Message-ID|MIME-Version|Content-Type|Content-Transfer-Encoding|X-[A-Za-z0-9\-]+):.*$",
    re.IGNORECASE,
)
_EMAIL_REPLY_HEADER = re.compile(r"^On .+ wrote:\s*$", re.IGNORECASE)
_EMAIL_SIGN_OFF = re.compile(
    r"^\s*(best regards|best|kind regards|regards|thanks|thank you|cheers|sincerely|yours truly|sent from my (iphone|android|mobile))\b",
    re.IGNORECASE,
)
_SIG_SEP = re.compile(r"^-{2,}\s*$")


class _HTMLStripper(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.chunks: list[str] = []

    def handle_data(self, data: str) -> None:  # type: ignore[override]
        self.chunks.append(data)


def _strip_html(s: str) -> str:
    if "<" not in s or ">" not in s:
        return s
    parser = _HTMLStripper()
    try:
        parser.feed(s)
    except Exception:
        return s
    return "".join(parser.chunks)


def _norm_email(text: str, target_sender: Optional[str]) -> str:
    text = _strip_html(text)
    out_lines: list[str] = []
    for ln in text.splitlines():
        stripped = ln.strip()
        if not stripped:
            out_lines.append("")
            continue
        if stripped.startswith(">"):
            continue
        if _EMAIL_HEADER_RE.match(stripped):
            continue
        if _EMAIL_REPLY_HEADER.match(stripped):
            break
        if _SIG_SEP.match(stripped):
            break
        if _EMAIL_SIGN_OFF.match(stripped):
            break
        out_lines.append(ln)
    return "\n".join(out_lines)


# ---------- Twitter / X ----------

_TW_JS_PREFIX = re.compile(r"^window\.[A-Za-z0-9_.]+\s*=\s*", re.MULTILINE)
_MENTION_PREFIX = re.compile(r"^(?:@\w+\s+)+")


def _norm_twitter(text: str, target_sender: Optional[str]) -> str:
    raw = _TW_JS_PREFIX.sub("", text.strip(), count=1)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return ""
    if not isinstance(data, list):
        return ""
    out: list[str] = []
    for item in data:
        tw = item.get("tweet") if isinstance(item, dict) else None
        if not isinstance(tw, dict):
            continue
        ft = tw.get("full_text") or tw.get("text") or ""
        if not ft:
            continue
        if ft.startswith("RT @"):
            continue
        ft = _MENTION_PREFIX.sub("", ft)
        ft = ft.strip()
        if ft:
            out.append(ft)
    return "\n".join(out)


# ---------- LinkedIn ----------


def _norm_linkedin(text: str, target_sender: Optional[str]) -> str:
    reader = csv.DictReader(io.StringIO(text))
    fields = {f.lower(): f for f in (reader.fieldnames or [])}
    out: list[str] = []
    if "sharecommentary" in fields:
        col = fields["sharecommentary"]
        for row in reader:
            v = (row.get(col) or "").strip()
            if v:
                out.append(v)
        return "\n".join(out)
    if "messagecontent" in fields:
        msg_col = fields["messagecontent"]
        sender_col = fields.get("from") or fields.get("sender") or fields.get("sendername")
        for row in reader:
            if target_sender and sender_col:
                if (row.get(sender_col) or "").strip() != target_sender.strip():
                    continue
            v = (row.get(msg_col) or "").strip()
            if v:
                out.append(v)
        return "\n".join(out)
    return ""


# ---------- Essay / Plain ----------

_NUMERIC_ONLY = re.compile(r"^\s*\d+\s*$")


def _norm_essay(text: str, target_sender: Optional[str]) -> str:
    lines = [ln for ln in text.splitlines() if not _NUMERIC_ONLY.match(ln)]
    return "\n".join(lines)


_DISPATCH = {
    "whatsapp": _norm_whatsapp,
    "telegram": _norm_telegram,
    "email": _norm_email,
    "twitter": _norm_twitter,
    "linkedin": _norm_linkedin,
    "essay": _norm_essay,
    "plain": _norm_essay,
}
