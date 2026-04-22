"""Phras backend entry point."""
from __future__ import annotations

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import auth as auth_routes
from routes import jobs as jobs_routes
from routes import style as style_routes
from routes import upload as upload_routes

app = FastAPI(title="Phras API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


app.include_router(auth_routes.router)
app.include_router(upload_routes.router)
app.include_router(jobs_routes.router)
app.include_router(style_routes.router)
