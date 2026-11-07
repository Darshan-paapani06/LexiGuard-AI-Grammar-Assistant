"""LexiGuard API + same-origin static web app."""
from pathlib import Path
from typing import Literal
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from . import engine, ml, secure_store

ROOT = Path(__file__).resolve().parent.parent
app = FastAPI(title="LexiGuard", version="1.0.0", description="Privacy-minded AI writing assistant")

class TextRequest(BaseModel):
    text: str = Field(max_length=20000)
    engine: Literal["built-in", "languagetool"] = "built-in"

class RewriteRequest(BaseModel):
    text: str = Field(min_length=1, max_length=8000)

class SaveRequest(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    content: str = Field(min_length=1, max_length=20000)
    passphrase: str = Field(min_length=8, max_length=256)

class UnlockRequest(BaseModel):
    passphrase: str = Field(min_length=1)

@app.get("/api/health")
def health():
    return {"status": "ok", "app": "LexiGuard", "version": "1.0.0"}

@app.post("/api/analyze")
def analyze(req: TextRequest):
    try:
        return engine.languagetool_analyze(req.text) if req.engine == "languagetool" else engine.analyze(req.text)
    except RuntimeError as exc:
        raise HTTPException(503, str(exc)) from exc

@app.post("/api/rewrite")
def rewrite(req: RewriteRequest):
    try:
        return {"rewritten": ml.rewrite(req.text), "model": "local transformer"}
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(503, str(exc)) from exc

@app.post("/api/vault", status_code=201)
def save_draft(req: SaveRequest):
    return secure_store.save(req.title, req.content, req.passphrase)

@app.get("/api/vault")
def list_drafts():
    return {"drafts": secure_store.list_drafts()}

@app.post("/api/vault/{draft_id}/unlock")
def unlock_draft(draft_id: str, req: UnlockRequest):
    try:
        draft = secure_store.load(draft_id, req.passphrase)
    except ValueError as exc:
        raise HTTPException(401, str(exc)) from exc
    if draft is None:
        raise HTTPException(404, "Draft not found")
    return draft

@app.delete("/api/vault/{draft_id}")
def delete_draft(draft_id: str):
    if not secure_store.remove(draft_id):
        raise HTTPException(404, "Draft not found")
    return {"deleted": True}

app.mount("/assets", StaticFiles(directory=ROOT / "frontend" / "assets"), name="assets")

@app.get("/")
def index():
    return FileResponse(ROOT / "frontend" / "index.html")
