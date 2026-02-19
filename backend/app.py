"""
NewsPulse API — FastAPI backend for the American politics news aggregator.
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .sources import SOURCES, CATEGORY_LABELS, LEAN_LABELS
from .fetcher import fetch_all_feeds
from .analyzer import analyze_topics
from .events import fetch_events

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="NewsPulse", description="American Politics News Aggregator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"


# Cache for results (simple in-memory)
_cache = {
    "news": None,
    "news_ts": None,
    "events": None,
    "events_ts": None,
}
CACHE_TTL_SECONDS = 180  # 3 minutes


@app.get("/api/scan")
async def scan_news(hours: int = Query(default=4, ge=1, le=24)):
    """
    Main endpoint: scan all sources, cluster topics, return analysis.
    """
    # Check cache
    if (
        _cache["news"]
        and _cache["news_ts"]
        and (datetime.now(timezone.utc) - _cache["news_ts"]).total_seconds() < CACHE_TTL_SECONDS
        and _cache.get("news_hours") == hours
    ):
        return JSONResponse(content=_cache["news"])

    logger.info(f"Starting news scan (last {hours} hours)...")

    # Fetch all feeds
    articles = await fetch_all_feeds(SOURCES, hours_back=hours)
    logger.info(f"Fetched {len(articles)} articles")

    # Analyze and cluster
    analysis = analyze_topics(articles)

    # Add source metadata
    analysis["source_registry"] = {
        "total_configured": len(SOURCES),
        "categories": CATEGORY_LABELS,
        "leans": LEAN_LABELS,
        "sources": [
            {"name": s["name"], "category": s["category"], "lean": s.get("lean", "center")}
            for s in SOURCES
        ],
    }

    # Cache
    _cache["news"] = analysis
    _cache["news_ts"] = datetime.now(timezone.utc)
    _cache["news_hours"] = hours

    return JSONResponse(content=analysis)


@app.get("/api/events")
async def get_events(days: int = Query(default=5, ge=1, le=14)):
    """
    Fetch upcoming newsworthy political events.
    """
    # Check cache
    if (
        _cache["events"]
        and _cache["events_ts"]
        and (datetime.now(timezone.utc) - _cache["events_ts"]).total_seconds() < CACHE_TTL_SECONDS
    ):
        return JSONResponse(content={"events": _cache["events"]})

    logger.info(f"Fetching events for next {days} days...")
    events = await fetch_events(days_ahead=days)

    _cache["events"] = events
    _cache["events_ts"] = datetime.now(timezone.utc)

    return JSONResponse(content={"events": events})


@app.get("/api/sources")
async def get_sources():
    """Return the full source registry."""
    return JSONResponse(content={
        "sources": [
            {
                "name": s["name"],
                "category": s["category"],
                "category_label": CATEGORY_LABELS.get(s["category"], s["category"]),
                "lean": s.get("lean", "center"),
                "lean_label": LEAN_LABELS.get(s.get("lean", "center"), "Center"),
                "url": s["url"],
            }
            for s in SOURCES
        ],
        "total": len(SOURCES),
        "categories": CATEGORY_LABELS,
        "leans": LEAN_LABELS,
    })


@app.get("/api/health")
async def health():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


# Serve frontend static files
if FRONTEND_DIR.exists():
    @app.get("/")
    async def serve_index():
        return FileResponse(FRONTEND_DIR / "index.html")

    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR)), name="frontend")
