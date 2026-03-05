import logging
import threading
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

from app.database import init_db, SessionLocal
from app.api import search, sources, ingest
from app.ingestion.ingest_all import ingest_all
from app.scripts.backfill_embeddings import backfill

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Content Search",
    description="Text retrieval application for movie/TV transcripts, books, and scripts",
    version="0.1.0",
)

app.include_router(search.router)
app.include_router(sources.router)
app.include_router(ingest.router)

# Serve the UI
static_dir = Path(__file__).parent / "static"
app.mount("/ui", StaticFiles(directory=str(static_dir), html=True), name="static")


@app.get("/")
def root():
    return RedirectResponse(url="/ui")


@app.on_event("startup")
def on_startup():
    init_db()
    db = SessionLocal()
    try:
        ingest_all(db)
    finally:
        db.close()
    # Backfill embeddings in background so the API starts immediately
    threading.Thread(target=backfill, daemon=True).start()


@app.get("/health")
def health():
    return {"status": "ok"}
