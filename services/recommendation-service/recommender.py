import json
import math
import random
from pathlib import Path
from typing import Any


def load_catalog(catalog_path: Path) -> list[dict[str, Any]]:
    with catalog_path.open(encoding="utf-8") as catalog_file:
        return json.load(catalog_file)


def cosine_similarity(left: list[float], right: list[float]) -> float:
    dot_product = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0 or right_norm == 0:
        return 0
    return dot_product / (left_norm * right_norm)


def default_user_vector(event_data: dict[str, Any] | None = None) -> list[float]:
    if not event_data:
        return [0.55, 0.45, 0.35, 0.50, 0.30]

    username = event_data.get("username", "").lower()
    email = event_data.get("email", "").lower()
    text = f"{username} {email}"
    return [
        0.70 if any(term in text for term in ["ai", "ml", "data"]) else 0.45,
        0.65 if any(term in text for term in ["dev", "api", "backend"]) else 0.40,
        0.65 if any(term in text for term in ["design", "ui", "frontend"]) else 0.35,
        0.70 if any(term in text for term in ["gpt", "llm", "gen"]) else 0.45,
        0.55,
    ]


def context_boost(item: dict[str, Any], context: str | None) -> float:
    if not context:
        return 0
    normalized_context = context.lower()
    return 0.12 if normalized_context in item["tags"] or normalized_context in item["title"].lower() else 0


def rank_items(
    catalog: list[dict[str, Any]],
    user_vector: list[float],
    context: str | None = None,
    limit: int = 5,
) -> list[dict[str, Any]]:
    ranked_items = []

    for item in catalog:
        semantic_score = cosine_similarity(user_vector, item["vector"])
        popularity_score = item["popularity"] * 0.15
        exploration_score = random.uniform(0, 0.03)
        final_score = semantic_score + popularity_score + context_boost(item, context) + exploration_score
        ranked_items.append(
            {
                "item_id": item["item_id"],
                "title": item["title"],
                "description": item["description"],
                "category": item["category"],
                "difficulty": item["difficulty"],
                "duration": item["duration"],
                "provider": item["provider"],
                "tags": item["tags"],
                "score": round(final_score, 4),
                "signals": {
                    "semantic_similarity": round(semantic_score, 4),
                    "popularity": item["popularity"],
                    "context": context,
                },
            }
        )

    ranked_items.sort(key=lambda item: item["score"], reverse=True)
    return ranked_items[:limit]


def update_profile_vector(
    current_vector: list[float],
    item_vector: list[float],
    event_type: str,
    rating: float | None = None,
) -> list[float]:
    weight = {"view": 0.10, "like": 0.22, "complete": 0.30}.get(event_type, 0.08)
    if rating is not None:
        weight += rating / 25

    return [
        round((current * (1 - weight)) + (incoming * weight), 4)
        for current, incoming in zip(current_vector, item_vector)
    ]
