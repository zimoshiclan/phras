"""API key verification middleware."""
from __future__ import annotations

import os
import secrets
from datetime import datetime, timezone
from hashlib import sha256

from fastapi import HTTPException, Request

from db.supabase_client import get_client


API_KEY_PREFIX = "phr_"


def hash_key(raw_key: str) -> str:
    salt = os.environ.get("API_KEY_SALT", "")
    return sha256((salt + raw_key).encode("utf-8")).hexdigest()


def generate_api_key() -> str:
    return API_KEY_PREFIX + secrets.token_urlsafe(32)


async def verify_api_key(request: Request) -> str:
    """Returns user_id for the authenticated API key. Raises 401 otherwise."""
    raw = request.headers.get("X-API-Key")
    if not raw:
        raise HTTPException(status_code=401, detail="missing X-API-Key")
    h = hash_key(raw)
    sb = get_client()
    res = sb.table("api_keys").select("id, user_id").eq("key_hash", h).limit(1).execute()
    rows = res.data or []
    if not rows:
        raise HTTPException(status_code=401, detail="invalid API key")
    user_id = rows[0]["user_id"]
    sb.table("api_keys").update({"last_used": datetime.now(timezone.utc).isoformat()}).eq("key_hash", h).execute()
    return user_id
