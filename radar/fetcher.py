"""
Async RSS/Atom fetcher for the US News Radar.
Handles parsing, deduplication, time-windowing, and per-source error recovery.
"""

import asyncio
import hashlib
import re
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from xml.etree import ElementTree as ET

import httpx
from dateutil import parser as dateparser

from .ad_filter import filter_ads

logger = logging.getLogger(__name__)

# XML namespaces used in RSS/Atom feeds
NS = {
    "atom":    "http://www.w3.org/2005/Atom",
    "dc":      "http://purl.org/dc/elements/1.1/",
    "content": "http://purl.org/rss/1.0/modules/content/",
    "media":   "http://search.yahoo.com/mrss/",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; USNewsRadar/1.0; "
        "+https://github.com/benno/us-news-radar)"
    ),
    "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*",
}

# Global seen-IDs set for within-scan deduplication
_seen_ids: set[str] = set()


# ── Helpers ────────────────────────────────────────────────────────────────────

def _parse_date(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    try:
        dt = dateparser.parse(s)
        if dt and dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def _strip_html(html: str) -> str:
    if not html:
        return ""
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&lt;",  "<", text)
    text = re.sub(r"&gt;",  ">", text)
    text = re.sub(r"&quot;","\"", text)
    text = re.sub(r"&#?\w+;", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _article_id(title: str, link: str) -> str:
    return hashlib.md5(f"{title}|{link}".encode()).hexdigest()


# ── RSS / Atom parsers ─────────────────────────────────────────────────────────

def _parse_rss_item(item: ET.Element) -> dict:
    title = item.findtext("title", "").strip()
    link  = item.findtext("link", "").strip()
    desc  = _strip_html(item.findtext("description", ""))
    pub   = _parse_date(
        item.findtext("pubDate") or item.findtext(f"{{{NS['dc']}}}date")
    )
    content = item.findtext(f"{{{NS['content']}}}encoded", "")
    full    = _strip_html(content) if content else desc
    return {
        "id":        _article_id(title, link),
        "title":     title,
        "link":      link,
        "summary":   desc[:600],
        "full_text": full[:2500],
        "published": pub,
    }


def _parse_atom_entry(entry: ET.Element) -> dict:
    title = entry.findtext(f"{{{NS['atom']}}}title", "").strip()
    link_el = (
        entry.find(f"{{{NS['atom']}}}link[@rel='alternate']")
        or entry.find(f"{{{NS['atom']}}}link")
    )
    link  = link_el.get("href", "") if link_el is not None else ""
    summ  = entry.findtext(f"{{{NS['atom']}}}summary", "")
    cont  = entry.findtext(f"{{{NS['atom']}}}content", "")
    desc  = _strip_html(cont or summ)
    pub   = _parse_date(
        entry.findtext(f"{{{NS['atom']}}}updated")
        or entry.findtext(f"{{{NS['atom']}}}published")
    )
    return {
        "id":        _article_id(title, link),
        "title":     title,
        "link":      link,
        "summary":   desc[:600],
        "full_text": desc[:2500],
        "published": pub,
    }


def _parse_xml(xml_text: str) -> list[dict]:
    """Parse RSS or Atom XML into article dicts."""
    # Fix unescaped ampersands
    xml_text = re.sub(r"&(?!amp;|lt;|gt;|quot;|apos;|#)", "&amp;", xml_text)
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        logger.warning("XML parse error: %s", exc)
        return []

    tag = root.tag.lower()
    articles = []

    if "feed" in tag:                           # Atom
        for entry in root.findall(f"{{{NS['atom']}}}entry"):
            articles.append(_parse_atom_entry(entry))
    else:                                       # RSS
        channel = root.find("channel")
        items = channel.findall("item") if channel is not None else root.findall(".//item")
        for item in items:
            articles.append(_parse_rss_item(item))

    return articles


# ── Per-source fetch ───────────────────────────────────────────────────────────

async def _fetch_url(client: httpx.AsyncClient, url: str) -> list[dict]:
    resp = await client.get(url, follow_redirects=True, timeout=15.0)
    resp.raise_for_status()
    return _parse_xml(resp.text)


async def fetch_source(
    client: httpx.AsyncClient,
    source: dict,
    cutoff: datetime,
) -> list[dict]:
    """Fetch one source, fall back to backup_url on failure."""
    raw: list[dict] = []
    for url_key in ("url", "backup_url"):
        url = source.get(url_key)
        if not url:
            continue
        try:
            raw = await _fetch_url(client, url)
            break
        except Exception as exc:
            logger.debug("Failed %s (%s): %s", source["name"], url, exc)

    if not raw:
        logger.info("No data fetched for: %s", source["name"])
        return []

    articles = []
    for art in raw:
        # Time filter: keep articles within window OR undated (assume recent)
        if art["published"] is not None and art["published"] < cutoff:
            continue
        # Enrich with source metadata
        art["source_name"]     = source["name"]
        art["source_category"] = source["category"]
        art["source_lean"]     = source.get("lean", "center")
        art["is_regional"]     = source.get("is_regional", False)
        art["region"]          = source.get("region")
        art["states"]          = source.get("states", [])
        articles.append(art)

    return articles


# ── Bulk fetch ─────────────────────────────────────────────────────────────────

async def fetch_all(
    sources: list[dict],
    hours_back: int = 6,
    filter_ads_flag: bool = True,
) -> dict:
    """
    Fetch all sources concurrently.

    Returns:
        {
          "articles": [...],
          "sources_ok": int,
          "sources_failed": int,
          "ads_removed": int,
        }
    """
    global _seen_ids
    _seen_ids = set()   # reset per scan

    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours_back)

    async with httpx.AsyncClient(headers=HEADERS) as client:
        tasks = [fetch_source(client, src, cutoff) for src in sources]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    all_articles: list[dict] = []
    sources_ok = 0
    sources_failed = 0

    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error("Exception for %s: %s", sources[i]["name"], result)
            sources_failed += 1
        elif isinstance(result, list):
            if result:
                sources_ok += 1
            all_articles.extend(result)
        else:
            sources_failed += 1

    # Deduplicate by article ID
    seen: set[str] = set()
    deduped: list[dict] = []
    for art in all_articles:
        if art["id"] not in seen:
            seen.add(art["id"])
            deduped.append(art)

    # Ad filter
    ads_removed = 0
    if filter_ads_flag:
        deduped, ads_removed = filter_ads(deduped)

    logger.info(
        "Fetched %d articles from %d sources (%d failed). "
        "After dedup+ad-filter: %d (removed %d ads)",
        len(all_articles), sources_ok, sources_failed,
        len(deduped), ads_removed,
    )

    return {
        "articles":       deduped,
        "sources_ok":     sources_ok,
        "sources_failed": sources_failed,
        "ads_removed":    ads_removed,
    }
