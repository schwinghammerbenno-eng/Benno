"""
Topic clustering and journalist-insight engine.

Pipeline:
  1. TF-IDF vectorise all article texts
  2. Agglomerative clustering → topic groups
  3. Rank by cross-source coverage
  4. Per-topic journalist insights:
     - Source diversity score
     - Political framing comparison (left vs right keywords)
     - Story freshness (new vs ongoing)
     - Source concentration warning
     - Underreported flag (regional > national coverage)
"""

import re
import logging
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
from typing import Optional

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────────

TOP_N_TOPICS = 20

NATIONAL_CATEGORIES = {
    "wire", "newspaper", "cable_news", "newsletter",
    "magazine", "think_tank", "nonprofit", "aggregator", "government",
}
REGIONAL_CATEGORIES = {"reg_newspaper", "reg_broadcast", "reg_nonprofit"}

# ── Text helpers ───────────────────────────────────────────────────────────────

def _text(article: dict) -> str:
    """Weight title 3× for clustering."""
    t = article.get("title", "")
    s = article.get("summary", "")
    return f"{t} {t} {t} {s}"


def _key_phrases(texts: list[str], top_n: int = 6) -> list[str]:
    if not texts:
        return []
    try:
        vec = TfidfVectorizer(
            max_features=300, stop_words="english",
            ngram_range=(1, 3), min_df=1, max_df=0.95,
        )
        mat = vec.fit_transform(texts)
        names = vec.get_feature_names_out()
        scores = mat.mean(axis=0).A1
        top = scores.argsort()[-top_n:][::-1]
        return [names[i] for i in top if scores[i] > 0]
    except Exception:
        return []


# ── Clustering ─────────────────────────────────────────────────────────────────

def _cluster(articles: list[dict], threshold: float = 0.22) -> list[list[dict]]:
    if not articles:
        return []
    if len(articles) == 1:
        return [articles]

    texts = [_text(a) for a in articles]
    try:
        vec = TfidfVectorizer(
            max_features=6000, stop_words="english",
            ngram_range=(1, 2), min_df=1, max_df=0.85,
        )
        mat = vec.fit_transform(texts)
    except ValueError:
        return [[a] for a in articles]

    sim = cosine_similarity(mat)
    dist = np.clip(1 - sim, 0, None)
    np.fill_diagonal(dist, 0)

    try:
        cl = AgglomerativeClustering(
            n_clusters=None,
            distance_threshold=1 - threshold,
            metric="precomputed",
            linkage="average",
        )
        labels = cl.fit_predict(dist)
    except Exception as exc:
        logger.warning("Clustering error: %s", exc)
        return [[a] for a in articles]

    groups: dict[int, list] = defaultdict(list)
    for idx, lbl in enumerate(labels):
        groups[lbl].append(articles[idx])

    return sorted(groups.values(), key=len, reverse=True)


# ── Per-topic journalist insights ──────────────────────────────────────────────

def _source_diversity(cluster: list[dict]) -> dict:
    """
    How diverse are the sources covering this topic?
    High diversity = covered by many different outlet *types* and *leans*.
    """
    cats  = set(a["source_category"] for a in cluster)
    leans = set(a.get("source_lean", "center") for a in cluster)
    names = set(a["source_name"] for a in cluster)

    national = sum(1 for a in cluster if a["source_category"] in NATIONAL_CATEGORIES)
    regional = sum(1 for a in cluster if a["source_category"] in REGIONAL_CATEGORIES)

    # Score 0-100: weight outlet count + category diversity + lean diversity
    score = min(100, len(names) * 4 + len(cats) * 8 + len(leans) * 6)

    return {
        "score": score,
        "outlet_count": len(names),
        "category_count": len(cats),
        "lean_count": len(leans),
        "national_articles": national,
        "regional_articles": regional,
        "label": (
            "Very High" if score >= 75 else
            "High"      if score >= 50 else
            "Moderate"  if score >= 30 else
            "Low"
        ),
    }


def _framing_comparison(cluster: list[dict]) -> list[dict]:
    """Compare how left-leaning vs right-leaning outlets frame the topic."""
    lean_groups: dict[str, list] = defaultdict(list)
    for a in cluster:
        lean = a.get("source_lean", "center")
        lean_groups[lean].append(a)

    result = []
    for lean, arts in lean_groups.items():
        titles = [a["title"] for a in arts if a.get("title")]
        phrases = _key_phrases(titles, top_n=3)
        if phrases:
            result.append({
                "lean":           lean,
                "article_count":  len(arts),
                "key_phrases":    phrases,
                "sample_headline": titles[0] if titles else "",
                "outlets":        list(set(a["source_name"] for a in arts))[:5],
            })

    # Sort: left → center → right
    order = {"left": 0, "center-left": 1, "center": 2, "center-right": 3, "right": 4}
    result.sort(key=lambda x: order.get(x["lean"], 5))
    return result


def _story_freshness(cluster: list[dict], now: datetime) -> dict:
    """Detect if story is brand new (<3h), active (<12h), or ongoing (>12h)."""
    dates = [a["published"] for a in cluster if a.get("published")]
    if not dates:
        return {"label": "Unknown", "oldest_hours_ago": None, "newest_hours_ago": None}

    newest = max(dates)
    oldest = min(dates)
    newest_age = (now - newest).total_seconds() / 3600
    oldest_age = (now - oldest).total_seconds() / 3600

    if newest_age < 3:
        label = "Breaking"
    elif newest_age < 12:
        label = "Active"
    elif oldest_age < 48:
        label = "Developing"
    else:
        label = "Ongoing"

    return {
        "label":            label,
        "newest_hours_ago": round(newest_age, 1),
        "oldest_hours_ago": round(oldest_age, 1),
    }


def _concentration_warning(cluster: list[dict]) -> Optional[str]:
    """Warn if a single source dominates coverage (>60 %)."""
    names = [a["source_name"] for a in cluster]
    if not names:
        return None
    top_name, top_count = Counter(names).most_common(1)[0]
    pct = top_count / len(names)
    if pct >= 0.6 and len(names) >= 4:
        return f"⚠ {top_name} accounts for {int(pct*100)}% of coverage — possible source concentration."
    return None


def _underreported_flag(cluster: list[dict]) -> bool:
    """
    True if the topic has more regional than national articles —
    could be a story gaining traction below the national radar.
    """
    national = sum(1 for a in cluster if a["source_category"] in NATIONAL_CATEGORIES)
    regional = sum(1 for a in cluster if a["source_category"] in REGIONAL_CATEGORIES)
    return regional > national and regional >= 3


# ── Main ───────────────────────────────────────────────────────────────────────

def analyze_topics(articles: list[dict]) -> dict:
    """
    Full topic analysis pipeline.

    Returns a dict with:
      topics         – top 20 ranked topic objects
      outliers       – smaller stories from niche/unique sources
      meta           – scan stats
    """
    now = datetime.now(timezone.utc)

    if not articles:
        return {
            "topics": [], "outliers": [],
            "meta": {"total_articles": 0, "total_sources": 0},
        }

    clusters = _cluster(articles)

    topics: list[dict] = []
    outliers: list[dict] = []

    all_sources = set(a["source_name"] for a in articles)

    for cluster in clusters:
        source_names = list(set(a["source_name"] for a in cluster))
        titles       = [a["title"] for a in cluster if a.get("title")]
        texts        = [a["title"] + " " + a.get("summary", "") for a in cluster]

        key_phrases  = _key_phrases(texts)
        headline     = max(titles, key=len) if titles else "(no title)"

        diversity    = _source_diversity(cluster)
        framing      = _framing_comparison(cluster)
        freshness    = _story_freshness(cluster, now)
        conc_warn    = _concentration_warning(cluster)
        underreported= _underreported_flag(cluster)

        # Time range
        dates  = [a["published"] for a in cluster if a.get("published")]
        pub_dates = sorted(dates) if dates else []

        entry = {
            "rank":           0,
            "headline":       headline,
            "key_phrases":    key_phrases,
            "article_count":  len(cluster),
            "source_count":   len(source_names),
            "sources":        source_names,
            "source_diversity": diversity,
            "framing_by_lean":  framing,
            "freshness":        freshness,
            "concentration_warning": conc_warn,
            "underreported":    underreported,
            "earliest":  pub_dates[0].isoformat()  if pub_dates else None,
            "latest":    pub_dates[-1].isoformat() if pub_dates else None,
            "articles": [
                {
                    "title":     a["title"],
                    "link":      a["link"],
                    "source":    a["source_name"],
                    "category":  a["source_category"],
                    "lean":      a.get("source_lean", "center"),
                    "region":    a.get("region"),
                    "is_regional": a.get("is_regional", False),
                    "published": a["published"].isoformat() if a.get("published") else None,
                    "summary":   a.get("summary", ""),
                }
                for a in cluster
            ],
        }

        # Outlier: covered by ≤2 sources and ≤3 articles
        if len(source_names) <= 2 and len(cluster) <= 3:
            outliers.append(entry)
        else:
            topics.append(entry)

    # Rank by (source_count DESC, article_count DESC)
    topics.sort(key=lambda t: (t["source_count"], t["article_count"]), reverse=True)
    topics = topics[:TOP_N_TOPICS]
    for i, t in enumerate(topics):
        t["rank"] = i + 1

    # Top 5 outliers, preferring nonprofit / think-tank sources
    outliers.sort(
        key=lambda t: (
            1 if any(
                c in ("think_tank", "nonprofit", "reg_nonprofit")
                for c in set(a["category"] for a in t["articles"])
            ) else 0,
            t["article_count"],
        ),
        reverse=True,
    )
    outliers = outliers[:5]
    for i, o in enumerate(outliers):
        o["rank"] = i + 1

    return {
        "topics":   topics,
        "outliers": outliers,
        "meta": {
            "total_articles": len(articles),
            "total_sources":  len(all_sources),
            "generated_at":   now.isoformat(),
        },
    }
