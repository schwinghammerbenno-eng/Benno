"""
Regional analysis module for the US News Radar.

Provides two analyses:
  A) Regional trends — top topics per US region
  B) Local framing detection — when a regional outlet covers a national story
     with a locally-specific angle (mentioning local places, officials, impact)
"""

import re
import logging
from collections import defaultdict, Counter
from typing import Optional

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .sources import REGIONS
from .topic_analyzer import _cluster, _key_phrases, _source_diversity

logger = logging.getLogger(__name__)

REGIONAL_CATEGORIES = {"reg_newspaper", "reg_broadcast", "reg_nonprofit"}
NATIONAL_CATEGORIES = {
    "wire", "newspaper", "cable_news", "newsletter",
    "magazine", "think_tank", "nonprofit", "aggregator", "government",
}

# ── Local angle detection ──────────────────────────────────────────────────────
# Signals that a regional article is localising a broader story

_LOCAL_SIGNALS = re.compile(
    r"\b("
    # Local economic impact patterns
    r"local\s+(?:jobs?|workers?|businesses?|economy|impact|residents?|families?|schools?)|"
    r"(?:our|the)\s+(?:state|city|county|district|region|community)|"
    # Government officials
    r"governor|state\s+legislature|state\s+senate|state\s+house|mayor|city\s+council|"
    r"state\s+(?:health\s+)?department|state\s+budget|state\s+officials?|"
    # Impact language
    r"affect(?:s|ing)?\s+(?:local|state|our)|"
    r"impact(?:s|ing)?\s+(?:local|state|our)|"
    r"(?:here\s+in|in\s+our)\s+\w+|"
    # Localisation phrases
    r"what\s+(?:this\s+)?means\s+for|how\s+(?:this\s+)?(?:will\s+)?affect|"
    r"locally|in\s+(?:our\s+)?(?:state|region|city|town|community)"
    r")\b",
    re.IGNORECASE,
)

# ── State / place-name recognition (lightweight, no spacy needed) ──────────────
# We check article text for state names and common major city names

STATE_NAMES = {
    "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado",
    "Connecticut", "Delaware", "Florida", "Georgia", "Hawaii", "Idaho",
    "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky", "Louisiana",
    "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota",
    "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada",
    "New Hampshire", "New Jersey", "New Mexico", "New York",
    "North Carolina", "North Dakota", "Ohio", "Oklahoma", "Oregon",
    "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota",
    "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington",
    "West Virginia", "Wisconsin", "Wyoming",
}
_STATE_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(s) for s in STATE_NAMES) + r")\b"
)


def _local_angle_score(article: dict) -> float:
    """
    Score 0–1 indicating how strongly a regional article localises a story.
    Combines:
      - Local-signal phrase density
      - Presence of state name matching the article's source state(s)
    """
    text = (article.get("title", "") + " " + article.get("summary", "")).lower()
    full = article.get("full_text", "").lower()
    combined = text + " " + full

    # Count local signals
    signal_hits = len(_LOCAL_SIGNALS.findall(combined))
    max_signals = 6
    signal_score = min(1.0, signal_hits / max_signals)

    # Check if article mentions own state(s)
    own_states = article.get("states", [])
    state_mentions = _STATE_PATTERN.findall(combined)
    state_hit = any(
        mention in STATE_NAMES and mention[:2].upper() in own_states
        or mention in own_states
        for mention in state_mentions
    ) if own_states else False

    return round(min(1.0, signal_score + (0.3 if state_hit else 0.0)), 3)


# ── Topic similarity ───────────────────────────────────────────────────────────

def _topic_match_score(
    regional_article: dict,
    national_topic: dict,
) -> float:
    """Cosine similarity between a regional article and a national topic cluster."""
    reg_text = regional_article.get("title", "") + " " + regional_article.get("summary", "")
    nat_texts = [
        a.get("title", "") + " " + a.get("summary", "")
        for a in national_topic.get("articles", [])[:20]
    ]
    if not reg_text.strip() or not nat_texts:
        return 0.0

    all_texts = [reg_text] + nat_texts
    try:
        vec = TfidfVectorizer(max_features=500, stop_words="english", ngram_range=(1, 2))
        mat = vec.fit_transform(all_texts)
        sims = cosine_similarity(mat[0:1], mat[1:]).flatten()
        return float(sims.max()) if len(sims) > 0 else 0.0
    except Exception:
        return 0.0


# ── Regional trend analysis ────────────────────────────────────────────────────

def analyze_regional(
    all_articles: list[dict],
    national_topics: list[dict],
    min_regional_articles: int = 2,
) -> dict:
    """
    Main regional analysis:
      1. Group regional articles by region
      2. Cluster per-region to find regional-specific top topics
      3. For each regional article that matches a national topic,
         compute local-angle score and flag localised coverage

    Returns:
        {
          "by_region": {
            "<region>": {
              "top_topics": [...],
              "local_framings": [...],
              "article_count": int,
              "source_count": int,
            }
          },
          "meta": { ... }
        }
    """
    # Separate regional vs national articles
    regional_arts = [a for a in all_articles if a.get("is_regional")]
    national_arts  = [a for a in all_articles if not a.get("is_regional")]

    # Group regional articles by region
    by_region: dict[str, list] = defaultdict(list)
    for art in regional_arts:
        r = art.get("region")
        if r:
            by_region[r].append(art)

    result: dict[str, dict] = {}

    for region in REGIONS:
        arts = by_region.get(region, [])
        if not arts:
            result[region] = {
                "top_topics":    [],
                "local_framings": [],
                "article_count": 0,
                "source_count":  0,
            }
            continue

        # Cluster regional articles to find regional-specific topics
        clusters = _cluster(arts, threshold=0.20)
        reg_topics = []
        for cl in sorted(clusters, key=len, reverse=True)[:10]:
            titles = [a["title"] for a in cl if a.get("title")]
            texts  = [a["title"] + " " + a.get("summary", "") for a in cl]
            reg_topics.append({
                "headline":    max(titles, key=len) if titles else "",
                "key_phrases": _key_phrases(texts, top_n=4),
                "article_count": len(cl),
                "sources": list(set(a["source_name"] for a in cl))[:6],
                "sample_articles": [
                    {
                        "title":   a["title"],
                        "link":    a["link"],
                        "source":  a["source_name"],
                        "published": a["published"].isoformat() if a.get("published") else None,
                    }
                    for a in cl[:3]
                ],
            })

        # Detect local framings of national stories
        local_framings = []
        SIMILARITY_THRESHOLD = 0.25
        LOCAL_ANGLE_THRESHOLD = 0.20

        for art in arts:
            for nat_topic in national_topics[:10]:   # check against top 10 national topics
                sim = _topic_match_score(art, nat_topic)
                if sim < SIMILARITY_THRESHOLD:
                    continue
                local_score = _local_angle_score(art)
                if local_score < LOCAL_ANGLE_THRESHOLD:
                    continue

                local_framings.append({
                    "regional_article": {
                        "title":     art["title"],
                        "link":      art["link"],
                        "source":    art["source_name"],
                        "published": art["published"].isoformat() if art.get("published") else None,
                        "summary":   art.get("summary", "")[:300],
                    },
                    "national_topic": {
                        "rank":        nat_topic.get("rank"),
                        "headline":    nat_topic.get("headline"),
                        "key_phrases": nat_topic.get("key_phrases", []),
                    },
                    "similarity_score":   round(sim, 3),
                    "local_angle_score":  local_score,
                    "local_angle_label":  (
                        "Strong local angle" if local_score >= 0.6 else
                        "Moderate local angle" if local_score >= 0.35 else
                        "Light local angle"
                    ),
                })

        # Deduplicate local_framings (keep highest similarity per article link)
        seen_links: dict[str, dict] = {}
        for lf in local_framings:
            link = lf["regional_article"]["link"]
            if link not in seen_links or lf["similarity_score"] > seen_links[link]["similarity_score"]:
                seen_links[link] = lf
        local_framings = sorted(
            seen_links.values(),
            key=lambda x: x["local_angle_score"],
            reverse=True,
        )[:15]

        result[region] = {
            "top_topics":     reg_topics,
            "local_framings": local_framings,
            "article_count":  len(arts),
            "source_count":   len(set(a["source_name"] for a in arts)),
        }

    return {
        "by_region": result,
        "meta": {
            "total_regional_articles": len(regional_arts),
            "total_national_articles": len(national_arts),
            "regions_with_data": [r for r in REGIONS if result.get(r, {}).get("article_count", 0) > 0],
        },
    }
