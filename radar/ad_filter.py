"""
Ad & sponsored-content filter for the US News Radar.

Strategy (no external model needed):
  1. URL path patterns that indicate ad/native content
  2. Title keyword patterns for sponsored/promotional text
  3. Summary keyword patterns
  4. Content-length heuristics (empty teaser = likely paywall or ad stub)
  5. Domain-level allow/block list (future extension point)
"""

import re
from typing import Optional

# ── Compiled patterns ──────────────────────────────────────────────────────────

# URL segments that strongly indicate sponsored / native-ad content
_AD_URL_PATTERNS = re.compile(
    r"/(sponsored[_-]?content?|advertorial|partner[_-]content|paid[_-]post|"
    r"brand[_-]studio|native[_-]ad|promo|promocontent|advertisement|"
    r"commercial|special[_-]report|presented[_-]by|partner[_-]post|"
    r"brandedcontent|custom[_-]content|content[_-]marketing)/",
    re.IGNORECASE,
)

# Title / headline patterns that signal ads or promotional content
_AD_TITLE_PATTERNS = re.compile(
    r"\b("
    r"sponsored|advertisement|advertorial|paid\s+post|partner\s+content|"
    r"presented\s+by|brought\s+to\s+you\s+by|paid\s+content|"
    r"brand\s+voice|native\s+ad|branded\s+content|"
    r"(?:shop|buy|order|get)\s+now|limited\s+time\s+offer|"
    r"\d+%\s*off|free\s+shipping|discount\s+code|promo\s+code|"
    r"best\s+(?:deals?|prices?|discounts?)|affiliate"
    r")\b",
    re.IGNORECASE,
)

# Summary / description patterns
_AD_SUMMARY_PATTERNS = re.compile(
    r"\b("
    r"click\s+here\s+to\s+(?:buy|shop|order|get)|"
    r"use\s+code\s+\w+\s+for|"
    r"exclusive\s+(?:deal|offer|discount)|"
    r"this\s+(?:article|post|content)\s+(?:is\s+)?(?:sponsored|paid|"
    r"presented|brought\s+to\s+you)"
    r")\b",
    re.IGNORECASE,
)

# Very short titles are usually teasers or placeholder stubs
_MIN_TITLE_LEN = 12

# Very short summaries with no useful info
_MIN_SUMMARY_LEN = 20


def is_ad(article: dict) -> bool:
    """
    Return True if the article appears to be sponsored / advertising content.
    False positives are possible but kept minimal; false negatives are acceptable.
    """
    title: str   = article.get("title", "") or ""
    link: str    = article.get("link", "") or ""
    summary: str = article.get("summary", "") or ""

    # 1. URL path check
    if _AD_URL_PATTERNS.search(link):
        return True

    # 2. Title keyword check
    if _AD_TITLE_PATTERNS.search(title):
        return True

    # 3. Summary keyword check
    if _AD_SUMMARY_PATTERNS.search(summary):
        return True

    # 4. Suspiciously short or empty title
    if len(title.strip()) < _MIN_TITLE_LEN:
        return True

    # 5. Title is ALL CAPS (classic clickbait / ad pattern)
    stripped = title.strip()
    if len(stripped) > 10 and stripped == stripped.upper() and stripped.isalpha():
        return True

    return False


def filter_ads(articles: list[dict]) -> tuple[list[dict], int]:
    """
    Filter a list of articles, removing detected ad content.

    Returns:
        (clean_articles, removed_count)
    """
    clean = []
    removed = 0
    for article in articles:
        if is_ad(article):
            removed += 1
        else:
            clean.append(article)
    return clean, removed


def ad_filter_report(articles: list[dict]) -> dict:
    """Return a summary dict for the ad-filtering step."""
    clean, removed = filter_ads(articles)
    return {
        "original_count": len(articles),
        "removed_count": removed,
        "clean_count": len(clean),
        "removal_rate_pct": round(removed / len(articles) * 100, 1) if articles else 0.0,
        "articles": clean,
    }
