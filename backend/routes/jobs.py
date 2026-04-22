"""Job status polling."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from db.supabase_client import get_client
from routes.security import verify_api_key

router = APIRouter(prefix="/v1", tags=["jobs"])


@router.get("/job/{job_id}")
def get_job(job_id: str, user_id: str = Depends(verify_api_key)):
    sb = get_client()
    res = (
        sb.table("upload_jobs")
        .select("id, status, style_id, error")
        .eq("id", job_id)
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    rows = res.data or []
    if not rows:
        raise HTTPException(status_code=404, detail="job not found")
    row = rows[0]
    return {
        "job_id": row["id"],
        "status": row["status"],
        "style_id": row.get("style_id"),
        "error": row.get("error"),
    }
