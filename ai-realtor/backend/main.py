from pathlib import Path
from dotenv import load_dotenv
from contextlib import asynccontextmanager
import logging

import os

_base_dir = Path(__file__).resolve().parent
load_dotenv(_base_dir / ".env")
load_dotenv(_base_dir / ".env.local", override=True)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import chat, ingest
from routers.ingest import auto_ingest_data_dir

logging.basicConfig(level=logging.INFO)

# CORS: allow localhost + production frontend URL (set CORS_ORIGINS in Render)
_CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
CORS_ORIGINS = [o.strip() for o in _CORS_ORIGINS if o.strip()]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Runs auto-ingestion of backend/data/ PDFs before the server accepts requests."""
    await auto_ingest_data_dir()
    yield


app = FastAPI(title="LLM Chat API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS if CORS_ORIGINS else ["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api")
app.include_router(ingest.router, prefix="/api")


@app.get("/health")
def health_check():
    return {"status": "ok"}
