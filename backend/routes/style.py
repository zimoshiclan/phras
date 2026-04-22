"""Style retrieval, refresh, profile, export, delete."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Query, UploadFile
import uuid

from db.supabase_client import get_client
from engine.formality import LEVELS, apply_context, apply_formality
from routes.security import verify_api_key
from routes.upload import _VALID_EXTS, _VALID_SOURCES, _BUCKET  # type: ignore

router = APIRouter(prefix="/v1", tags=["style"])


def _load_profile(sb, style_id: str, user_id: str) -> dict:
    res = (
        sb.table("style_profiles")
        .select("id, style_vector, cached_constraints, corpus_word_count, source_types, label, updated_at")
        .eq("id", style_id)
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    rows = res.data or []
    if not rows:
        raise HTTPException(status_code=404, detail="style not found")
    return rows[0]


@router.get("/style/{style_id}")
def get_style(
    style_id: str,
    formality: str = Query(...),
    context: Optional[str] = Query(None),
    user_id: str = Depends(verify_api_key),
):
    if formality not in LEVELS:
        raise HTTPException(status_code=400, detail=f"formality must be one of {sorted(LEVELS)}")
    _VALID_CONTEXTS = {"email", "reply", "tweet", "linkedin", "general"}
    if context is not None and context not in _VALID_CONTEXTS:
        raise HTTPException(status_code=400, detail=f"context must be one of {sorted(_VALID_CONTEXTS)}")
    sb = get_client()
    prof = _load_profile(sb, style_id, user_id)
    cache_key = f"{formality}:{context or 'none'}"
    cache: dict = prof.get("cached_constraints") or {}
    if cache_key in cache:
        constraint = cache[cache_key]
    else:
        constraint = apply_formality(prof["style_vector"], formality)
        constraint = apply_context(constraint, context)
        cache[cache_key] = constraint
        sb.table("style_profiles").update({"cached_constraints": cache}).eq("id", style_id).eq("user_id", user_id).execute()
    return {
        "style_id": style_id,
        "formality": formality,
        "context": context,
        "constraint": constraint,
    }


@router.get("/style/{style_id}/profile")
def get_profile(style_id: str, user_id: str = Depends(verify_api_key)):
    sb = get_client()
    prof = _load_profile(sb, style_id, user_id)
    vector = dict(prof["style_vector"])
    vector.pop("function_words", None)
    return {
        "style_id": style_id,
        "label": prof.get("label"),
        "corpus_word_count": prof.get("corpus_word_count"),
        "source_types": prof.get("source_types"),
        "updated_at": prof.get("updated_at"),
        "style_vector": vector,
    }


@router.post("/style/{style_id}/refresh")
async def refresh_style(
    style_id: str,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    source: str = Form(...),
    target_sender: Optional[str] = Form(None),
    user_id: str = Depends(verify_api_key),
):
    if source not in _VALID_SOURCES:
        raise HTTPException(status_code=400, detail="invalid source")
    ext = "." + (file.filename or "").rsplit(".", 1)[-1].lower() if "." in (file.filename or "") else ""
    if ext not in _VALID_EXTS:
        raise HTTPException(status_code=400, detail=f"unsupported file type: {ext}")

    sb = get_client()
    _load_profile(sb, style_id, user_id)
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="empty file")
    if len(raw) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="file too large \u2014 10 MB max")

    job_id = str(uuid.uuid4())
    storage_path = f"{user_id}/{job_id}/original{ext}"
    try:
        sb.storage.from_(_BUCKET).upload(storage_path, raw, {"upsert": "true"})
    except Exception:
        raise HTTPException(status_code=500, detail="file storage failed \u2014 please retry")

    sb.table("upload_jobs").insert({
        "id": job_id,
        "user_id": user_id,
        "style_id": style_id,
        "status": "pending",
        "source": source,
        "storage_path": storage_path,
    }).execute()

    background_tasks.add_task(_refresh_analysis, job_id, user_id, style_id, raw, source, target_sender, storage_path)
    return {"job_id": job_id, "status": "processing"}


def _refresh_analysis(job_id: str, user_id: str, style_id: str, raw_bytes: bytes,
                      source: str, target_sender: Optional[str], storage_path: str) -> None:
    from engine.extractor import extract_features
    from engine.normalizers import normalize

    sb = get_client()
    try:
        sb.table("upload_jobs").update({"status": "processing"}).eq("id", job_id).execute()
        text = raw_bytes.decode("utf-8", errors="replace")
        clean = normalize(text, source, target_sender)
        if not clean.strip():
            raise ValueError("normalization produced empty text")
        new_vec = extract_features(clean)
        existing = _load_profile(sb, style_id, user_id)
        merged = _merge_vectors(existing["style_vector"], new_vec, new_weight=0.4)
        source_types = list(set((existing.get("source_types") or []) + [source]))
        sb.table("style_profiles").update({
            "style_vector": merged,
            "cached_constraints": {},
            "source_types": source_types,
            "corpus_word_count": (existing.get("corpus_word_count") or 0) + new_vec["corpus_stats"]["word_count"],
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", style_id).eq("user_id", user_id).execute()
        sb.table("upload_jobs").update({
            "status": "complete",
            "style_id": style_id,
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "storage_path": None,
        }).eq("id", job_id).execute()
        try:
            sb.storage.from_(_BUCKET).remove([storage_path])
        except Exception:
            pass
    except Exception as exc:
        sb.table("upload_jobs").update({
            "status": "failed",
            "error": str(exc)[:500],
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", job_id).execute()
        try:
            sb.storage.from_(_BUCKET).remove([storage_path])
        except Exception:
            pass


def _merge_vectors(old: dict, new: dict, new_weight: float = 0.4) -> dict:
    w = new_weight

    def blend(a, b):
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            return (1 - w) * a + w * b
        if isinstance(a, dict) and isinstance(b, dict):
            keys = set(a) | set(b)
            return {k: blend(a.get(k, 0), b.get(k, 0)) if isinstance(a.get(k, b.get(k)), (int, float, dict))
                    else b.get(k, a.get(k)) for k in keys}
        return b if b not in (None, [], "", {}) else a

    return blend(old, new)


@router.delete("/style/{style_id}", status_code=204)
def delete_style(style_id: str, user_id: str = Depends(verify_api_key)):
    sb = get_client()
    _load_profile(sb, style_id, user_id)
    sb.table("style_profiles").delete().eq("id", style_id).eq("user_id", user_id).execute()
    return


@router.get("/account/export")
def export_account(user_id: str = Depends(verify_api_key)):
    sb = get_client()
    res = sb.table("style_profiles").select("*").eq("user_id", user_id).execute()
    return {"style_profiles": res.data or []}
