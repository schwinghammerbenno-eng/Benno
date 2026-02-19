"""
Topic extraction, clustering, and cross-source analysis engine.
Uses TF-IDF + cosine similarity for topic clustering, no external NLP models.
"""

import re
import math
import logging
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Optional

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

logger = logging.getLogger(__name__)

# Stop words extended for news context
NEWS_STOP_WORDS = {
    "said", "says", "would", "could", "also", "new", "one", "two",
    "like", "just", "get", "make", "year", "years", "time", "first",
    "last", "week", "day", "today", "monday", "tuesday", "wednesday",
    "thursday", "friday", "saturday", "sunday", "according", "report",
    "reports", "news", "breaking", "update", "latest", "analysis",
    "opinion", "editorial", "us", "u.s.", "america", "american",
    "americans", "united", "states",
}


def _combine_text(article: dict) -> str:
    """Combine title and summary for analysis, weighting title heavily."""
    title = article.get("title", "")
    summary = article.get("summary", "")
    # Repeat title 3x to weight it more in TF-IDF
    return f"{title} {title} {title} {summary}"


def _extract_key_phrases(texts: list[str], top_n: int = 5) -> list[str]:
    """Extract top key phrases from a cluster of texts using TF-IDF."""
    if not texts:
        return []
    try:
        vectorizer = TfidfVectorizer(
            max_features=200,
            stop_words="english",
            ngram_range=(1, 3),
            min_df=1,
            max_df=0.9,
        )
        tfidf = vectorizer.fit_transform(texts)
        feature_names = vectorizer.get_feature_names_out()
        # Average TF-IDF scores across documents
        avg_scores = tfidf.mean(axis=0).A1
        top_indices = avg_scores.argsort()[-top_n:][::-1]
        return [feature_names[i] for i in top_indices if avg_scores[i] > 0]
    except Exception:
        return []


def cluster_articles(articles: list[dict], similarity_threshold: float = 0.20) -> list[list[dict]]:
    """
    Cluster articles into topic groups using TF-IDF + agglomerative clustering.
    Returns list of clusters (each cluster = list of articles about the same topic).
    """
    if not articles:
        return []

    if len(articles) == 1:
        return [articles]

    texts = [_combine_text(a) for a in articles]

    try:
        vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words="english",
            ngram_range=(1, 2),
            min_df=1,
            max_df=0.85,
        )
        tfidf_matrix = vectorizer.fit_transform(texts)
    except ValueError:
        # If vectorizer fails (e.g. all stop words), treat each article as its own cluster
        return [[a] for a in articles]

    # Cosine similarity
    sim_matrix = cosine_similarity(tfidf_matrix)
    # Convert to distance for clustering
    distance_matrix = 1 - sim_matrix
    np.fill_diagonal(distance_matrix, 0)
    distance_matrix = np.clip(distance_matrix, 0, None)

    try:
        clustering = AgglomerativeClustering(
            n_clusters=None,
            distance_threshold=1 - similarity_threshold,
            metric="precomputed",
            linkage="average",
        )
        labels = clustering.fit_predict(distance_matrix)
    except Exception as e:
        logger.warning(f"Clustering failed: {e}")
        return [[a] for a in articles]

    # Group articles by cluster label
    clusters_map = defaultdict(list)
    for idx, label in enumerate(labels):
        clusters_map[label].append(articles[idx])

    # Sort clusters by size (most covered first)
    clusters = sorted(clusters_map.values(), key=len, reverse=True)
    return clusters


def _compute_source_alignment(articles: list[dict]) -> dict:
    """
    Analyze how aligned different sources are on a topic.
    Returns alignment score and details.
    """
    if len(articles) <= 1:
        return {"score": 0, "details": "Single source coverage"}

    source_texts = {}
    for a in articles:
        name = a["source_name"]
        if name not in source_texts:
            source_texts[name] = ""
        source_texts[name] += " " + a.get("title", "") + " " + a.get("summary", "")

    if len(source_texts) <= 1:
        return {"score": 100, "details": "Only one source"}

    texts = list(source_texts.values())
    names = list(source_texts.keys())

    try:
        vectorizer = TfidfVectorizer(stop_words="english", max_features=500)
        tfidf = vectorizer.fit_transform(texts)
        sim = cosine_similarity(tfidf)
        # Average pairwise similarity
        n = len(texts)
        total_sim = 0
        count = 0
        for i in range(n):
            for j in range(i + 1, n):
                total_sim += sim[i][j]
                count += 1
        avg_sim = total_sim / count if count > 0 else 0
        alignment_pct = int(avg_sim * 100)
    except Exception:
        alignment_pct = 50

    return {
        "score": alignment_pct,
        "details": (
            "High consensus" if alignment_pct > 70
            else "Moderate agreement" if alignment_pct > 40
            else "Divergent perspectives"
        ),
    }


def _detect_perspective_differences(articles: list[dict]) -> list[dict]:
    """
    Detect where different-leaning sources differ on framing.
    """
    lean_groups = defaultdict(list)
    for a in articles:
        lean = a.get("source_lean", "center")
        lean_groups[lean].append(a)

    differences = []
    leans = list(lean_groups.keys())

    if len(leans) < 2:
        return differences

    for lean, group_articles in lean_groups.items():
        # Combine titles from this lean
        titles = [a["title"] for a in group_articles]
        key_phrases = _extract_key_phrases(titles, top_n=3)
        if key_phrases:
            sources = list(set(a["source_name"] for a in group_articles))
            differences.append({
                "perspective": lean,
                "sources": sources,
                "emphasis": key_phrases,
                "sample_headline": titles[0] if titles else "",
            })

    return differences


def analyze_topics(articles: list[dict]) -> dict:
    """
    Main analysis pipeline:
    1. Cluster articles into topics
    2. Rank by coverage count
    3. Analyze source alignment and perspective differences
    4. Identify outliers
    """
    if not articles:
        return {"topics": [], "outliers": [], "meta": {"total_articles": 0, "total_sources": 0}}

    clusters = cluster_articles(articles)

    topics = []
    outlier_candidates = []

    all_source_names = set(a["source_name"] for a in articles)
    all_source_categories = set(a["source_category"] for a in articles)

    for cluster in clusters:
        # Basic info
        source_names = list(set(a["source_name"] for a in cluster))
        source_categories = list(set(a["source_category"] for a in cluster))
        source_leans = list(set(a["source_lean"] for a in cluster))

        # Representative title (most common significant words)
        titles = [a["title"] for a in cluster]
        key_phrases = _extract_key_phrases(
            [a["title"] + " " + a.get("summary", "") for a in cluster],
            top_n=5,
        )

        # Best representative title = longest one
        representative_title = max(titles, key=len) if titles else ""

        # Source alignment analysis
        alignment = _compute_source_alignment(cluster)

        # Perspective differences
        perspectives = _detect_perspective_differences(cluster)

        # Time range
        pub_dates = [a["published"] for a in cluster if a.get("published")]
        earliest = min(pub_dates) if pub_dates else None
        latest = max(pub_dates) if pub_dates else None

        # Count articles per category
        cat_counts = Counter(a["source_category"] for a in cluster)

        topic_entry = {
            "rank": 0,  # filled later
            "headline": representative_title,
            "key_phrases": key_phrases,
            "article_count": len(cluster),
            "source_count": len(source_names),
            "sources": source_names,
            "source_categories": source_categories,
            "source_leans": source_leans,
            "category_counts": dict(cat_counts),
            "alignment": alignment,
            "perspectives": perspectives,
            "earliest": earliest.isoformat() if earliest else None,
            "latest": latest.isoformat() if latest else None,
            "articles": [
                {
                    "title": a["title"],
                    "link": a["link"],
                    "source": a["source_name"],
                    "source_category": a["source_category"],
                    "source_lean": a["source_lean"],
                    "published": a["published"].isoformat() if a.get("published") else None,
                    "summary": a.get("summary", ""),
                }
                for a in cluster
            ],
        }

        if len(source_names) <= 2 and len(cluster) <= 3:
            outlier_candidates.append(topic_entry)
        else:
            topics.append(topic_entry)

    # Sort topics by source_count (cross-source coverage), then article_count
    topics.sort(key=lambda t: (t["source_count"], t["article_count"]), reverse=True)

    # Assign ranks
    for i, t in enumerate(topics):
        t["rank"] = i + 1

    # Pick top 3 outliers — ones with interesting content from fewer sources
    # Prefer outliers that come from think tanks or podcasts (more unique perspective)
    outlier_candidates.sort(
        key=lambda t: (
            1 if any(c in ("think_tank", "podcast") for c in t["source_categories"]) else 0,
            t["article_count"],
        ),
        reverse=True,
    )
    outliers = outlier_candidates[:3]
    for i, o in enumerate(outliers):
        o["rank"] = i + 1

    return {
        "topics": topics,
        "outliers": outliers,
        "meta": {
            "total_articles": len(articles),
            "total_sources": len(all_source_names),
            "source_categories": list(all_source_categories),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
    }
