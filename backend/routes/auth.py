"""Auth routes: register, login. Thin passthrough to Supabase Auth."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr

from db.supabase_client import get_client
from routes.security import generate_api_key, hash_key

router = APIRouter(prefix="/auth", tags=["auth"])


class Credentials(BaseModel):
    email: EmailStr
    password: str


@router.post("/register")
def register(body: Credentials):
    sb = get_client()
    try:
        result = sb.auth.sign_up({"email": body.email, "password": body.password})
    except Exception:
        raise HTTPException(status_code=400, detail="registration failed — check email format and password length")
    user = getattr(result, "user", None)
    if not user:
        raise HTTPException(status_code=400, detail="registration failed")
    user_id = user.id
    raw_key = generate_api_key()
    sb.table("api_keys").insert({
        "user_id": user_id,
        "key_hash": hash_key(raw_key),
        "label": "default",
    }).execute()
    return {"user_id": user_id, "api_key": raw_key}


@router.post("/login")
def login(body: Credentials):
    sb = get_client()
    try:
        result = sb.auth.sign_in_with_password({"email": body.email, "password": body.password})
    except Exception:
        raise HTTPException(status_code=401, detail="invalid credentials")
    session = getattr(result, "session", None)
    if not session:
        raise HTTPException(status_code=401, detail="invalid credentials")
    return {"access_token": session.access_token, "refresh_token": session.refresh_token}
