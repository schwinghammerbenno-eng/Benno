"""
Async fetcher for RSS/Atom feeds and web pages.
Handles parsing without feedparser (uses lxml + custom logic).
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

logger = logging.getLogger(__name__)

# Common namespaces in RSS/Atom
NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "dc": "http://purl.org/dc/elements/1.1/",
    "content": "http://purl.org/rss/1.0/modules/content/",
    "media": "http://search.yahoo.com/mrss/",
}

HEADERS = {
    "User-Agent": "NewsPulse/1.0 (News Aggregator; +https://github.com/newspulse)",
    "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*",
}


def _parse_date(date_str: Optional[str]) -> Optional[datetime]:
    """Parse various date formats found in RSS/Atom feeds."""
    if not date_str:
        return None
    try:
        dt = dateparser.parse(date_str)
        if dt and dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return None


def _strip_html(html: str) -> str:
    """Remove HTML tags from a string."""
    if not html:
        return ""
    clean = re.sub(r"<[^>]+>", " ", html)
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean


def _make_id(title: str, link: str) -> str:
    """Create a unique ID from title + link."""
    raw = f"{title}|{link}"
    return hashlib.md5(raw.encode()).hexdigest()


def _parse_rss_item(item: ET.Element) -> dict:
    """Parse a single RSS <item> element."""
    title = item.findtext("title", "").strip()
    link = item.findtext("link", "").strip()
    description = _strip_html(item.findtext("description", ""))
    pub_date = _parse_date(
        item.findtext("pubDate")
        or item.findtext(f"{{{NS['dc']}}}date")
    )
    # Try to get full content
    content_encoded = item.findtext(f"{{{NS['content']}}}encoded", "")
    full_text = _strip_html(content_encoded) if content_encoded else description

    return {
        "id": _make_id(title, link),
        "title": title,
        "link": link,
        "summary": description[:500] if description else "",
        "full_text": full_text[:2000] if full_text else "",
        "published": pub_date,
    }


def _parse_atom_entry(entry: ET.Element) -> dict:
    """Parse a single Atom <entry> element."""
    title = entry.findtext(f"{{{NS['atom']}}}title", "").strip()

    link_el = entry.find(f"{{{NS['atom']}}}link[@rel='alternate']")
    if link_el is None:
        link_el = entry.find(f"{{{NS['atom']}}}link")
    link = link_el.get("href", "") if link_el is not None else ""

    summary_el = entry.findtext(f"{{{NS['atom']}}}summary", "")
    content_el = entry.findtext(f"{{{NS['atom']}}}content", "")
    description = _strip_html(content_el or summary_el)

    pub_date = _parse_date(
        entry.findtext(f"{{{NS['atom']}}}updated")
        or entry.findtext(f"{{{NS['atom']}}}published")
    )

    return {
        "id": _make_id(title, link),
        "title": title,
        "link": link,
        "summary": description[:500] if description else "",
        "full_text": description[:2000] if description else "",
        "published": pub_date,
    }


def parse_feed_xml(xml_text: str) -> list[dict]:
    """Parse RSS or Atom XML into a list of article dicts."""
    articles = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        # Try fixing common issues
        xml_text = re.sub(r"&(?!amp;|lt;|gt;|quot;|apos;|#)", "&amp;", xml_text)
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError:
            logger.warning("Failed to parse XML feed")
            return []

    # Detect feed type
    tag = root.tag.lower()

    if "feed" in tag:
        # Atom feed
        for entry in root.findall(f"{{{NS['atom']}}}entry"):
            articles.append(_parse_atom_entry(entry))
    else:
        # RSS feed — look for <channel><item>
        channel = root.find("channel")
        if channel is None:
            # Some feeds put items directly under root or rss
            items = root.findall(".//item")
        else:
            items = channel.findall("item")
        for item in items:
            articles.append(_parse_rss_item(item))

    return articles


async def fetch_feed(
    client: httpx.AsyncClient,
    source: dict,
    hours_back: int = 6,
) -> list[dict]:
    """
    Fetch a single RSS/Atom feed and return articles within the time window.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours_back)
    url = source["url"]
    articles = []

    try:
        resp = await client.get(url, follow_redirects=True, timeout=15.0)
        resp.raise_for_status()
        raw_articles = parse_feed_xml(resp.text)

        for art in raw_articles:
            art["source_name"] = source["name"]
            art["source_category"] = source["category"]
            art["source_lean"] = source.get("lean", "center")
            # Keep articles within the time window OR if no date (include them as recent)
            if art["published"] is None or art["published"] >= cutoff:
                articles.append(art)

    except Exception as e:
        logger.warning(f"Failed to fetch {source['name']} ({url}): {e}")
        # Try backup URL if available
        backup = source.get("backup_url")
        if backup:
            try:
                resp = await client.get(backup, follow_redirects=True, timeout=15.0)
                resp.raise_for_status()
                raw_articles = parse_feed_xml(resp.text)
                for art in raw_articles:
                    art["source_name"] = source["name"]
                    art["source_category"] = source["category"]
                    art["source_lean"] = source.get("lean", "center")
                    if art["published"] is None or art["published"] >= cutoff:
                        articles.append(art)
            except Exception as e2:
                logger.warning(f"Backup also failed for {source['name']}: {e2}")

    return articles


async def fetch_all_feeds(
    sources: list[dict],
    hours_back: int = 6,
) -> list[dict]:
    """Fetch all sources concurrently and return combined article list."""
    async with httpx.AsyncClient(headers=HEADERS) as client:
        tasks = [fetch_feed(client, src, hours_back) for src in sources]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    all_articles = []
    sources_reached = 0
    sources_failed = 0

    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(f"Exception fetching {sources[i]['name']}: {result}")
            sources_failed += 1
        elif isinstance(result, list):
            if result:
                sources_reached += 1
            all_articles.extend(result)
        else:
            sources_failed += 1

    logger.info(
        f"Fetched {len(all_articles)} articles from {sources_reached} sources "
        f"({sources_failed} failed)"
    )
    return all_articles
