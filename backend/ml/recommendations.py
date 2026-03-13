"""
ml/recommendations.py
═══════════════════════════════════════════════════════════════
AI Recommendation Engine for Smart Cafe.

Three-tier recommendation strategy:
  1. Collaborative Filtering  — "customers who ordered X also ordered Y"
     Uses item-item co-occurrence matrix built from order history.

  2. Content-Based             — match items with similar tags/category
     to items the customer has ordered before.

  3. Popularity Fallback       — when no history exists, return
     most-ordered / highest-rated items.

No heavy ML library required — runs on pure Python + numpy.
Scikit-learn is used optionally for cosine similarity.
"""
from __future__ import annotations
import logging
from collections import defaultdict
from typing import List, Dict, Any, Optional
import math

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
#  Co-occurrence builder
# ─────────────────────────────────────────────────────────────

def build_cooccurrence(order_items_rows: List[Dict]) -> Dict[str, Dict[str, int]]:
    """
    Build item-item co-occurrence matrix from raw order_items rows.
    Input: list of {"order_id": str, "menu_item_id": str}
    Returns: {item_a: {item_b: count_shared_orders}}
    """
    # Group items by order
    orders: Dict[str, set] = defaultdict(set)
    for row in order_items_rows:
        orders[row["order_id"]].add(row["menu_item_id"])

    cooc: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for items in orders.values():
        items_list = list(items)
        for i, item_a in enumerate(items_list):
            for item_b in items_list[i+1:]:
                cooc[item_a][item_b] += 1
                cooc[item_b][item_a] += 1

    return {k: dict(v) for k, v in cooc.items()}


def cosine_similarity_items(
    item_a: str,
    item_b: str,
    cooc: Dict[str, Dict[str, int]]
) -> float:
    """Simple cosine similarity between two items' co-occurrence vectors."""
    vec_a = cooc.get(item_a, {})
    vec_b = cooc.get(item_b, {})
    common = set(vec_a) & set(vec_b)
    if not common:
        return 0.0
    dot = sum(vec_a[k] * vec_b[k] for k in common)
    norm_a = math.sqrt(sum(v**2 for v in vec_a.values()))
    norm_b = math.sqrt(sum(v**2 for v in vec_b.values()))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


# ─────────────────────────────────────────────────────────────
#  Recommendation functions
# ─────────────────────────────────────────────────────────────

def collaborative_recommendations(
    ordered_item_ids: List[str],
    cooc: Dict[str, Dict[str, int]],
    all_items: List[Dict],
    top_n: int = 5
) -> List[Dict]:
    """
    Given a list of item IDs the customer has ordered,
    return top_n recommended items using co-occurrence scores.
    """
    scores: Dict[str, float] = defaultdict(float)
    already_ordered = set(ordered_item_ids)

    for item_id in ordered_item_ids:
        neighbours = cooc.get(item_id, {})
        for neighbour, count in neighbours.items():
            if neighbour not in already_ordered:
                scores[neighbour] += count

    # Normalise
    if scores:
        max_score = max(scores.values())
        for k in scores:
            scores[k] /= max_score

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_n]
    ranked_ids = {r[0]: r[1] for r in ranked}

    result = []
    for item in all_items:
        if item["id"] in ranked_ids:
            result.append({
                **item,
                "_rec_score": round(ranked_ids[item["id"]], 3),
                "_rec_reason": "Others who ordered your items also loved this"
            })

    return sorted(result, key=lambda x: x["_rec_score"], reverse=True)


def content_based_recommendations(
    ordered_items_data: List[Dict],
    all_items: List[Dict],
    top_n: int = 5
) -> List[Dict]:
    """
    Tag/category-based content similarity.
    Recommend items sharing tags/category with what the customer ordered.
    """
    if not ordered_items_data:
        return []

    # Build preference profile from ordered items
    ordered_ids     = {i["id"] for i in ordered_items_data}
    liked_tags: Dict[str, int]       = defaultdict(int)
    liked_categories: Dict[str, int] = defaultdict(int)

    for item in ordered_items_data:
        liked_categories[item.get("category", "")] += 2
        for tag in (item.get("tags") or []):
            liked_tags[tag] += 1

    def item_score(item: Dict) -> float:
        if item["id"] in ordered_ids:
            return -1.0
        score = 0.0
        score += liked_categories.get(item.get("category", ""), 0) * 1.5
        for tag in (item.get("tags") or []):
            score += liked_tags.get(tag, 0) * 1.0
        return score

    scored = [(item, item_score(item)) for item in all_items if item.get("is_available")]
    scored = [(i, s) for i, s in scored if s > 0]
    scored.sort(key=lambda x: x[1], reverse=True)

    return [{
        **item,
        "_rec_score":  round(score, 3),
        "_rec_reason": f"Based on your love of {item.get('category', 'similar items')}"
    } for item, score in scored[:top_n]]


def popularity_recommendations(
    all_items: List[Dict],
    order_counts: Dict[str, int],
    exclude_ids: Optional[set] = None,
    top_n: int = 5
) -> List[Dict]:
    """Popularity-based fallback: most ordered available items."""
    exclude_ids = exclude_ids or set()
    available = [i for i in all_items if i.get("is_available") and i["id"] not in exclude_ids]
    scored = [(i, order_counts.get(i["id"], 0) + (5 if i.get("is_featured") else 0)) for i in available]
    scored.sort(key=lambda x: x[1], reverse=True)
    return [{
        **item,
        "_rec_score":  count,
        "_rec_reason": "Popular with our customers"
    } for item, count in scored[:top_n]]


# ─────────────────────────────────────────────────────────────
#  Main entry point
# ─────────────────────────────────────────────────────────────

def get_recommendations(
    customer_order_history: List[Dict],   # list of order rows with order_items
    all_items: List[Dict],                # all menu_items rows
    all_order_items: List[Dict],          # all order_items rows (for co-occurrence)
    top_n: int = 5
) -> Dict[str, Any]:
    """
    Master recommendation function.
    Returns {
        "recommendations": [...],
        "strategy":        "collaborative" | "content_based" | "popular",
        "based_on":        list of item names the customer previously ordered
    }
    """
    # Flatten ordered items from history
    ordered_item_ids = []
    ordered_items_data = []
    for order in customer_order_history:
        for oi in (order.get("order_items") or []):
            mid = oi.get("menu_item_id")
            if mid:
                ordered_item_ids.append(mid)
                if oi.get("menu_items"):
                    ordered_items_data.append(oi["menu_items"])

    # Build item popularity counts
    count_map: Dict[str, int] = defaultdict(int)
    for oi in all_order_items:
        count_map[oi["menu_item_id"]] += oi["quantity"]

    # Strategy selection
    if len(ordered_item_ids) >= 2:
        # Enough history → try collaborative first
        cooc = build_cooccurrence(all_order_items)
        recs = collaborative_recommendations(ordered_item_ids, cooc, all_items, top_n)
        if recs:
            return {
                "recommendations": recs,
                "strategy": "collaborative",
                "based_on": list({i.get("name", "") for i in ordered_items_data})[:3]
            }

    if ordered_items_data:
        # Some history → content-based
        recs = content_based_recommendations(ordered_items_data, all_items, top_n)
        if recs:
            return {
                "recommendations": recs,
                "strategy": "content_based",
                "based_on": list({i.get("name", "") for i in ordered_items_data})[:3]
            }

    # Cold start → popularity
    recs = popularity_recommendations(all_items, count_map, set(ordered_item_ids), top_n)
    return {
        "recommendations": recs,
        "strategy": "popular",
        "based_on": []
    }