"""Upload + background analysis."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile

from db.supabase_client import get_client
from engine.extractor import extract_features
from engine.normalizers import normalize
from routes.security import verify_api_key

router = APIRouter(prefix="/v1", tags=["upload"])

_VALID_SOURCES = {"whatsapp", "telegram", "email", "twitter", "linkedin", "essay", "plain"}
_VALID_EXTS = {".txt", ".csv", ".json", ".eml", ".js"}
_BUCKET = "raw-uploads"


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_analysis(job_id: str, user_id: str, raw_bytes: bytes, source: str,
                 target_sender: Optional[str], storage_path: str) -> None:
    sb = get_client()
    try:
        sb.table("upload_jobs").update({"status": "processing"}).eq("id", job_id).execute()
        text = raw_bytes.decode("utf-8", errors="replace")
        clean = normalize(text, source, target_sender)
        if not clean.strip():
            raise ValueError("normalization produced empty text")
        vector = extract_features(clean)
        style_row = sb.table("style_profiles").insert({
            "user_id": user_id,
            "style_vector": vector,
            "corpus_word_count": vector.get("corpus_stats", {}).get("word_count", 0),
            "source_types": [source],
        }).execute()
        style_id = style_row.data[0]["id"]
        sb.table("upload_jobs").update({
            "status": "complete",
            "style_id": style_id,
            "completed_at": _iso_now(),
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
            "completed_at": _iso_now(),
        }).eq("id", job_id).execute()
        try:
            sb.storage.from_(_BUCKET).remove([storage_path])
        except Exception:
            pass


@router.post("/upload")
async def upload(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    source: str = Form(...),
    target_sender: Optional[str] = Form(None),
    user_id: str = Depends(verify_api_key),
):
    if source not in _VALID_SOURCES:
        raise HTTPException(status_code=400, detail=f"source must be one of {sorted(_VALID_SOURCES)}")
    ext = "." + (file.filename or "").rsplit(".", 1)[-1].lower() if "." in (file.filename or "") else ""
    if ext not in _VALID_EXTS:
        raise HTTPException(status_code=400, detail=f"unsupported file type: {ext}")

    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="empty file")
    if len(raw) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="file too large \u2014 10 MB max")

    sb = get_client()
    job_id = str(uuid.uuid4())
    storage_path = f"{user_id}/{job_id}/original{ext}"

    try:
        sb.storage.from_(_BUCKET).upload(storage_path, raw, {"upsert": "true"})
    except Exception:
        raise HTTPException(status_code=500, detail="file storage failed \u2014 please retry")

    sb.table("upload_jobs").insert({
        "id": job_id,
        "user_id": user_id,
        "status": "pending",
        "source": source,
        "storage_path": storage_path,
    }).execute()

    background_tasks.add_task(run_analysis, job_id, user_id, raw, source, target_sender, storage_path)
    return {"job_id": job_id, "status": "processing"}
