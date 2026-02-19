"""
Upcoming political events schedule scraper.
Pulls from government calendars, C-SPAN, congressional schedules,
and news calendar sources.
"""

import asyncio
import re
import logging
from datetime import datetime, timezone, timedelta
from xml.etree import ElementTree as ET

import httpx
from bs4 import BeautifulSoup
from dateutil import parser as dateparser

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "NewsPulse/1.0 (News Aggregator)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

EVENT_SOURCES = [
    {
        "name": "C-SPAN Schedule",
        "url": "https://www.c-span.org/schedule/",
        "type": "html",
        "parser": "cspan",
    },
    {
        "name": "Senate Floor Schedule",
        "url": "https://www.senate.gov/legislative/schedule.htm",
        "type": "html",
        "parser": "senate",
    },
    {
        "name": "House Floor Schedule",
        "url": "https://live.house.gov/",
        "type": "html",
        "parser": "house",
    },
    {
        "name": "White House Schedule",
        "url": "https://www.whitehouse.gov/schedule/",
        "type": "html",
        "parser": "whitehouse",
    },
    {
        "name": "Reuters Events Calendar",
        "url": "https://www.reuters.com/markets/us/events/",
        "type": "html",
        "parser": "reuters_events",
    },
    {
        "name": "Politico Calendar",
        "url": "https://www.politico.com/",
        "type": "html",
        "parser": "politico_cal",
    },
    {
        "name": "Google News - Upcoming US Events",
        "url": "https://news.google.com/rss/search?q=upcoming+scheduled+hearing+vote+congress+summit+press+conference+when:3d&hl=en-US&gl=US",
        "type": "rss",
        "parser": "gnews_events",
    },
]


def _parse_date_safe(date_str: str) -> datetime | None:
    """Safely parse a date string."""
    if not date_str:
        return None
    try:
        dt = dateparser.parse(date_str)
        if dt and dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def _extract_events_from_html(html: str, parser_type: str) -> list[dict]:
    """Extract events from HTML based on the parser type."""
    soup = BeautifulSoup(html, "lxml")
    events = []

    if parser_type == "cspan":
        # C-SPAN schedule - look for schedule items
        for item in soup.select(".schedule-item, .program-item, tr, li"):
            text = item.get_text(strip=True, separator=" ")
            if len(text) > 20 and any(
                kw in text.lower()
                for kw in [
                    "hearing", "session", "debate", "press", "vote",
                    "committee", "conference", "speech", "address",
                    "briefing", "forum", "summit", "testimony",
                ]
            ):
                # Try to find a date/time
                time_el = item.select_one(".time, .date, time")
                time_str = time_el.get_text(strip=True) if time_el else ""
                events.append({
                    "title": text[:200],
                    "time_str": time_str,
                    "source": "C-SPAN",
                })

    elif parser_type == "senate":
        # Focus on the main content area, skip navigation
        main = soup.select_one("#main-content, .main-content, main, #content, .contenttext")
        container = main if main else soup
        for item in container.select("p, li, tr"):
            text = item.get_text(strip=True, separator=" ")
            # Filter: must be long enough to be real content, not nav
            if len(text) > 40 and len(text) < 500 and any(
                kw in text.lower()
                for kw in [
                    "convene", "vote", "hearing", "recess",
                    "amendment", "cloture", "quorum",
                    "a.m.", "p.m.", "o'clock",
                ]
            ):
                events.append({
                    "title": text[:200],
                    "time_str": "",
                    "source": "Senate",
                })

    elif parser_type == "house":
        main = soup.select_one("#main-content, .main-content, main, #content")
        container = main if main else soup
        for item in container.select("p, li, tr"):
            text = item.get_text(strip=True, separator=" ")
            if len(text) > 40 and len(text) < 500 and any(
                kw in text.lower()
                for kw in [
                    "vote", "hearing", "session", "rule",
                    "suspension", "consideration", "bill",
                    "a.m.", "p.m.", "o'clock",
                ]
            ):
                events.append({
                    "title": text[:200],
                    "time_str": "",
                    "source": "House",
                })

    elif parser_type == "whitehouse":
        for item in soup.select("article, .schedule-item, li, p"):
            text = item.get_text(strip=True, separator=" ")
            if len(text) > 15 and any(
                kw in text.lower()
                for kw in [
                    "president", "briefing", "meeting", "summit",
                    "remarks", "signing", "ceremony", "address",
                    "press", "travel",
                ]
            ):
                time_el = item.select_one("time, .date")
                time_str = time_el.get_text(strip=True) if time_el else ""
                events.append({
                    "title": text[:200],
                    "time_str": time_str,
                    "source": "White House",
                })

    elif parser_type == "reuters_events":
        for item in soup.select(".event-item, tr, li, article"):
            text = item.get_text(strip=True, separator=" ")
            if len(text) > 20 and any(
                kw in text.lower()
                for kw in [
                    "fed", "fomc", "treasury", "economic", "data",
                    "report", "conference", "summit", "hearing",
                ]
            ):
                events.append({
                    "title": text[:200],
                    "time_str": "",
                    "source": "Reuters",
                })

    elif parser_type == "politico_cal":
        for item in soup.select("article, .story-text, h3, h2"):
            text = item.get_text(strip=True, separator=" ")
            if any(
                kw in text.lower()
                for kw in [
                    "scheduled", "upcoming", "expected", "set to",
                    "will vote", "to hold", "hearing on",
                ]
            ):
                events.append({
                    "title": text[:200],
                    "time_str": "",
                    "source": "Politico",
                })

    return events


def _extract_events_from_rss(xml_text: str) -> list[dict]:
    """Extract event-like articles from an RSS feed."""
    events = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return events

    items = root.findall(".//item")
    for item in items:
        title = item.findtext("title", "").strip()
        pub_date = item.findtext("pubDate", "")
        description = item.findtext("description", "")
        link = item.findtext("link", "")

        # Check if title mentions scheduled events
        combined = f"{title} {description}".lower()
        if any(
            kw in combined
            for kw in [
                "hearing", "vote", "scheduled", "upcoming",
                "set to", "press conference", "summit", "meeting",
                "testimony", "trial", "ruling", "deadline",
                "launch", "ceremony", "speech", "address",
            ]
        ):
            events.append({
                "title": title,
                "time_str": pub_date,
                "source": "Google News",
                "link": link,
                "description": re.sub(r"<[^>]+>", "", description)[:300],
            })

    return events


async def fetch_events(days_ahead: int = 5) -> list[dict]:
    """Fetch upcoming political events from multiple sources."""
    all_events = []

    async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True) as client:
        tasks = []
        for src in EVENT_SOURCES:
            tasks.append(_fetch_single_source(client, src))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(results):
            if isinstance(result, list):
                all_events.extend(result)
            elif isinstance(result, Exception):
                logger.warning(f"Event source {EVENT_SOURCES[i]['name']} failed: {result}")

    # De-duplicate by title similarity
    seen_titles = set()
    unique_events = []
    for ev in all_events:
        title_lower = ev["title"].lower().strip()
        # Simple dedup: skip if we've seen a very similar title
        title_key = re.sub(r"[^a-z0-9]", "", title_lower)[:50]
        if title_key not in seen_titles:
            seen_titles.add(title_key)
            # Parse the time
            ev["parsed_date"] = _parse_date_safe(ev.get("time_str", ""))
            unique_events.append(ev)

    # Sort by date (items with dates first, then undated)
    now = datetime.now(timezone.utc)
    cutoff = now + timedelta(days=days_ahead)

    dated = [e for e in unique_events if e.get("parsed_date")]
    undated = [e for e in unique_events if not e.get("parsed_date")]

    # Filter to only upcoming
    dated = [e for e in dated if e["parsed_date"] >= now - timedelta(hours=2)]
    dated = [e for e in dated if e["parsed_date"] <= cutoff]
    dated.sort(key=lambda e: e["parsed_date"])

    # Format output
    formatted = []
    for ev in dated + undated[:10]:
        formatted.append({
            "title": ev["title"],
            "date": ev["parsed_date"].isoformat() if ev.get("parsed_date") else None,
            "date_display": (
                ev["parsed_date"].strftime("%a, %b %d %Y %I:%M %p ET")
                if ev.get("parsed_date") else "Date TBD"
            ),
            "source": ev.get("source", "Unknown"),
            "link": ev.get("link", ""),
            "description": ev.get("description", ""),
        })

    return formatted


async def _fetch_single_source(client: httpx.AsyncClient, source: dict) -> list[dict]:
    """Fetch events from a single source."""
    try:
        resp = await client.get(source["url"], timeout=15.0)
        resp.raise_for_status()

        if source["type"] == "rss":
            return _extract_events_from_rss(resp.text)
        else:
            return _extract_events_from_html(resp.text, source["parser"])
    except Exception as e:
        logger.warning(f"Failed to fetch events from {source['name']}: {e}")
        return []
