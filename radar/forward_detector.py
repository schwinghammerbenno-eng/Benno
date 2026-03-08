"""
Forward-looking event detector for the US News Radar.

Scans hundreds of headlines for linguistic signals of upcoming events:
  - Explicit future dates ("next Tuesday", "March 15", "in two weeks")
  - Deadline language ("due by", "deadline", "expires")
  - Scheduled proceedings ("hearing", "vote", "ruling expected", "summit")
  - Election / campaign signals
  - Economic data release language ("report due", "data release", "Fed meeting")
  - Legislative signals ("bill goes to", "markup", "floor vote")

Output: ranked list of "upcoming events" with supporting headlines,
        event type, urgency, and source diversity.
"""

import re
import logging
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from typing import Optional

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

# ── Pattern definitions ────────────────────────────────────────────────────────

# Future time references
_FUTURE_TIME = re.compile(
    r"\b("
    r"next\s+(?:week|month|monday|tuesday|wednesday|thursday|friday|saturday|sunday|year)|"
    r"this\s+(?:week|month|friday|weekend|coming\s+week)|"
    r"(?:by|before|until|ahead\s+of)\s+(?:the\s+)?(?:end\s+of\s+)?(?:january|february|march|"
    r"april|may|june|july|august|september|october|november|december|next\s+\w+)|"
    r"in\s+(?:the\s+)?(?:coming|next)\s+(?:days?|weeks?|months?)|"
    r"(?:january|february|march|april|may|june|july|august|september|october|november|december)"
    r"\s+\d{1,2}(?:st|nd|rd|th)?(?:\s*,\s*20\d{2})?|"
    r"\d{1,2}\s+(?:days?|weeks?|months?)\s+from\s+now|"
    r"upcoming|soon|imminent|on\s+(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)"
    r")\b",
    re.IGNORECASE,
)

# Event type classifiers — each maps to a category
_EVENT_PATTERNS: list[tuple[str, str, int]] = [
    # (regex, event_type, urgency 1-5)
    (r"\b(senate|house|congress)\s+(?:vote|votes|voting|to\s+vote|floor\s+vote|markup)\b",                 "Legislative Vote",      5),
    (r"\b(bill|legislation|resolution)\s+(?:goes?\s+to|expected\s+to\s+(?:pass|fail)|will\s+be\s+voted)\b","Legislative Vote",      4),
    (r"\b(?:supreme\s+court|appeals?\s+court|federal\s+court)\s+(?:hears?|ruling|decision|hearing)\b",     "Court Ruling / Hearing", 5),
    (r"\b(?:oral\s+arguments?|court\s+ruling\s+expected|verdict\s+expected)\b",                            "Court Ruling / Hearing", 5),
    (r"\b(?:deadline|expires?|expiring|due\s+(?:date|by)|must\s+(?:act|vote|decide)\s+by)\b",              "Deadline",              5),
    (r"\b(?:federal\s+reserve|fed|fomc)\s+(?:meeting|decision|rate\s+(?:hike|cut|decision))\b",            "Fed / Economic Policy", 4),
    (r"\b(?:jobs\s+report|cpi|inflation\s+data|gdp\s+(?:data|report)|earnings\s+report)\s+(?:due|expected|coming|release)\b", "Economic Data Release", 4),
    (r"\b(?:press\s+conference|news\s+conference|briefing)\s+(?:scheduled|planned|expected)\b",            "Press Conference",      3),
    (r"\b(?:summit|state\s+visit|diplomatic\s+meeting|foreign\s+minister|secretary\s+of\s+state)\s+(?:to\s+meet|meeting|visits?|scheduled)\b", "Diplomatic Event", 4),
    (r"\b(?:primary|election|ballot|polling|campaign)\s+(?:day|season|filing\s+deadline)\b",               "Election / Campaign",   5),
    (r"\b(?:government\s+shutdown|continuing\s+resolution|debt\s+ceiling|budget\s+deadline)\b",            "Budget / Fiscal",       5),
    (r"\b(?:executive\s+order|presidential\s+proclamation)\s+(?:expected|planned|coming)\b",               "Executive Action",      4),
    (r"\b(?:confirmation\s+hearing|senate\s+confirmation)\b",                                              "Senate Confirmation",   4),
    (r"\b(?:natural\s+disaster|hurricane\s+season|wildfire\s+season|flood\s+warning)\s+(?:expected|forecast|approaching)\b", "Natural Disaster Risk", 3),
    (r"\b(?:treaty|agreement|deal|accord)\s+(?:expires?|renewal|renegotiat|talks?)\b",                     "Treaty / Agreement",    3),
    (r"\b(?:tariff|trade\s+war|sanction)\s+(?:takes?\s+effect|deadline|effective\s+(?:date|on))\b",        "Trade / Tariffs",       4),
    (r"\b(?:vaccine|drug)\s+(?:approval|authorization)\s+(?:expected|decision|hearing)\b",                 "Health / FDA",          4),
    (r"\b(?:report|investigation|audit|probe)\s+(?:due|expected|release|concludes?)\b",                    "Report / Investigation", 3),
    (r"\b(?:state\s+of\s+the\s+union|inaugural|address\s+to\s+congress)\b",                               "Major Speech",          4),
    (r"\b(?:trial\s+(?:begins?|starts?|scheduled|set\s+to\s+begin))\b",                                   "Trial",                 4),
]

_COMPILED_EVENTS = [
    (re.compile(pattern, re.IGNORECASE), etype, urgency)
    for pattern, etype, urgency in _EVENT_PATTERNS
]


# ── Per-article event detection ────────────────────────────────────────────────

def _detect_events_in_article(article: dict) -> list[dict]:
    """
    Return list of detected forward-looking signals in one article.
    Each signal: {event_type, urgency, matched_text, has_future_ref}
    """
    title   = article.get("title", "") or ""
    summary = article.get("summary", "") or ""
    text    = title + " " + summary

    has_future = bool(_FUTURE_TIME.search(text))
    signals = []

    for pattern, etype, urgency in _COMPILED_EVENTS:
        m = pattern.search(text)
        if m:
            signals.append({
                "event_type":    etype,
                "urgency":       urgency + (1 if has_future else 0),
                "matched_text":  m.group(0),
                "has_future_ref": has_future,
            })

    return signals


# ── Cluster forward-looking articles into events ───────────────────────────────

def _group_event_articles(tagged: list[dict]) -> dict[str, list]:
    """Group articles by their primary event type."""
    by_type: dict[str, list] = defaultdict(list)
    for item in tagged:
        for sig in item["signals"]:
            by_type[sig["event_type"]].append(item["article"])
    return by_type


def _dedupe_by_similarity(articles: list[dict], threshold: float = 0.30) -> list[dict]:
    """Remove near-duplicate articles within an event group."""
    if len(articles) <= 1:
        return articles
    texts = [a.get("title", "") + " " + a.get("summary", "") for a in articles]
    try:
        vec = TfidfVectorizer(max_features=500, stop_words="english")
        mat = vec.fit_transform(texts)
        sim = cosine_similarity(mat)
        keep = []
        excluded = set()
        for i in range(len(articles)):
            if i in excluded:
                continue
            keep.append(articles[i])
            for j in range(i + 1, len(articles)):
                if sim[i][j] >= threshold:
                    excluded.add(j)
        return keep
    except Exception:
        return articles


# ── Main ───────────────────────────────────────────────────────────────────────

def detect_forward_events(articles: list[dict], top_n: int = 15) -> dict:
    """
    Scan all articles for forward-looking event signals.

    Returns:
        {
          "events": [
            {
              "event_type":     str,
              "urgency":        int (1-6),
              "article_count":  int,
              "source_count":   int,
              "key_signals":    [str],   -- matched phrases
              "supporting_articles": [...],
              "sources":        [str],
            },
            ...
          ],
          "meta": { ... }
        }
    """
    tagged: list[dict] = []

    for article in articles:
        sigs = _detect_events_in_article(article)
        if sigs:
            tagged.append({"article": article, "signals": sigs})

    # Group by event type
    by_type = _group_event_articles(tagged)

    events = []
    for etype, arts in by_type.items():
        if len(arts) < 1:
            continue

        # Deduplicate
        arts = _dedupe_by_similarity(arts)

        # Urgency = max urgency across all signals for this type
        max_urgency = max(
            sig["urgency"]
            for item in tagged
            for sig in item["signals"]
            if sig["event_type"] == etype
        )

        key_signals = list(set(
            sig["matched_text"]
            for item in tagged
            for sig in item["signals"]
            if sig["event_type"] == etype
        ))[:6]

        sources = list(set(a["source_name"] for a in arts))

        events.append({
            "event_type":   etype,
            "urgency":      min(max_urgency, 6),
            "urgency_label": (
                "Critical" if max_urgency >= 6 else
                "High"     if max_urgency >= 5 else
                "Medium"   if max_urgency >= 3 else
                "Low"
            ),
            "article_count": len(arts),
            "source_count":  len(sources),
            "sources":       sources[:8],
            "key_signals":   key_signals,
            "supporting_articles": [
                {
                    "title":     a.get("title", ""),
                    "link":      a.get("link", ""),
                    "source":    a.get("source_name", ""),
                    "published": a["published"].isoformat() if a.get("published") else None,
                    "summary":   a.get("summary", "")[:250],
                    "region":    a.get("region"),
                }
                for a in arts[:5]
            ],
        })

    # Sort by urgency DESC, then article_count DESC
    events.sort(key=lambda e: (e["urgency"], e["article_count"]), reverse=True)
    events = events[:top_n]

    return {
        "events": events,
        "meta": {
            "articles_scanned":   len(articles),
            "articles_with_signals": len(tagged),
            "event_types_found":  len(events),
            "signal_rate_pct":    round(len(tagged) / len(articles) * 100, 1) if articles else 0.0,
        },
    }
