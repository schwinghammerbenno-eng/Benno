"""
US News Radar — FastAPI backend.

Endpoints:
  GET /api/scan           — full scan (top topics + regional + forward events)
  GET /api/topics         — top 20 national topics only
  GET /api/regional       — regional trend analysis
  GET /api/forward        — upcoming events forecast
  GET /api/sources        — source registry
  GET /api/health         — liveness check
"""

import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .sources import SOURCES, CATEGORY_LABELS, LEAN_LABELS, REGIONS
from .fetcher import fetch_all
from .topic_analyzer import analyze_topics
from .regional_analyzer import analyze_regional
from .forward_detector import detect_forward_events

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="US News Radar",
    description="Scans ~200 US news sources for top topics, regional trends & upcoming events.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UI_DIR = Path(__file__).parent.parent / "radar_ui"

# ── Simple in-memory cache ─────────────────────────────────────────────────────
_cache: dict = {}
CACHE_TTL = 240  # seconds


def _cache_valid(key: str, hours: int) -> bool:
    entry = _cache.get(key)
    if not entry:
        return False
    age = (datetime.now(timezone.utc) - entry["ts"]).total_seconds()
    return age < CACHE_TTL and entry.get("hours") == hours


# ── Full scan helper ───────────────────────────────────────────────────────────

async def _run_scan(hours: int) -> dict:
    """Fetch, analyse, and return the complete radar result."""
    fetch_result = await fetch_all(SOURCES, hours_back=hours, filter_ads_flag=True)
    articles = fetch_result["articles"]

    # Parallel analysis
    topic_result   = analyze_topics(articles)
    regional_result = analyze_regional(articles, topic_result["topics"])
    forward_result  = detect_forward_events(articles)

    return {
        "topics":         topic_result["topics"],
        "outliers":       topic_result["outliers"],
        "regional":       regional_result,
        "forward_events": forward_result,
        "meta": {
            **topic_result["meta"],
            "sources_queried":    len(SOURCES),
            "sources_ok":         fetch_result["sources_ok"],
            "sources_failed":     fetch_result["sources_failed"],
            "ads_removed":        fetch_result["ads_removed"],
            "hours_back":         hours,
            "regions_analysed":   len(REGIONS),
        },
    }


# ── Endpoints ──────────────────────────────────────────────────────────────────

@app.get("/api/scan")
async def full_scan(hours: int = Query(default=6, ge=1, le=48)):
    """
    Full radar scan — returns top 20 topics, regional analysis,
    upcoming-event forecast, and meta stats.
    Cached for 4 minutes.
    """
    cache_key = "full_scan"
    if _cache_valid(cache_key, hours):
        return JSONResponse(content=_cache[cache_key]["data"])

    logger.info("Running full scan (hours_back=%d)…", hours)
    result = await _run_scan(hours)

    _cache[cache_key] = {
        "data":  result,
        "ts":    datetime.now(timezone.utc),
        "hours": hours,
    }
    return JSONResponse(content=result)


@app.get("/api/topics")
async def get_topics(hours: int = Query(default=6, ge=1, le=48)):
    """Top 20 national news topics with journalist insights."""
    cache_key = "full_scan"
    if not _cache_valid(cache_key, hours):
        logger.info("Topics: running fresh scan…")
        result = await _run_scan(hours)
        _cache[cache_key] = {"data": result, "ts": datetime.now(timezone.utc), "hours": hours}
    data = _cache[cache_key]["data"]
    return JSONResponse(content={
        "topics":   data["topics"],
        "outliers": data["outliers"],
        "meta":     data["meta"],
    })


@app.get("/api/regional")
async def get_regional(hours: int = Query(default=6, ge=1, le=48)):
    """Regional trends and local-framing analysis per US region."""
    cache_key = "full_scan"
    if not _cache_valid(cache_key, hours):
        logger.info("Regional: running fresh scan…")
        result = await _run_scan(hours)
        _cache[cache_key] = {"data": result, "ts": datetime.now(timezone.utc), "hours": hours}
    data = _cache[cache_key]["data"]
    return JSONResponse(content=data["regional"])


@app.get("/api/forward")
async def get_forward_events(hours: int = Query(default=12, ge=1, le=48)):
    """Upcoming newsworthy events detected from current headlines."""
    cache_key = "full_scan"
    if not _cache_valid(cache_key, hours):
        logger.info("Forward events: running fresh scan…")
        result = await _run_scan(hours)
        _cache[cache_key] = {"data": result, "ts": datetime.now(timezone.utc), "hours": hours}
    data = _cache[cache_key]["data"]
    return JSONResponse(content=data["forward_events"])


@app.get("/api/sources")
async def list_sources():
    """Return the full source registry with metadata."""
    national = [s for s in SOURCES if not s.get("is_regional")]
    regional = [s for s in SOURCES if s.get("is_regional")]

    by_region: dict[str, list] = {}
    for s in regional:
        r = s.get("region", "Unknown")
        by_region.setdefault(r, []).append({
            "name":     s["name"],
            "category": s["category"],
            "lean":     s.get("lean", "center"),
            "states":   s.get("states", []),
        })

    return JSONResponse(content={
        "total":         len(SOURCES),
        "national_count": len(national),
        "regional_count": len(regional),
        "national": [
            {
                "name":           s["name"],
                "category":       s["category"],
                "category_label": CATEGORY_LABELS.get(s["category"], s["category"]),
                "lean":           s.get("lean", "center"),
                "lean_label":     LEAN_LABELS.get(s.get("lean", "center"), ""),
            }
            for s in national
        ],
        "by_region": by_region,
        "regions":   REGIONS,
        "categories": CATEGORY_LABELS,
        "leans":      LEAN_LABELS,
    })


@app.get("/api/health")
async def health():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


# ── Serve UI ───────────────────────────────────────────────────────────────────
if UI_DIR.exists():
    @app.get("/")
    async def serve_ui():
        return FileResponse(UI_DIR / "index.html")

    app.mount("/", StaticFiles(directory=str(UI_DIR)), name="ui")
