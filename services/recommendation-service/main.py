import asyncio
import json
import math
import os
import random
import threading
import time
from pathlib import Path
from typing import Any

import redis
from fastapi import FastAPI
from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable
from pydantic import BaseModel, Field


app = FastAPI(
    title="Microverse Recommendation AI Service",
    description="Hybrid AI recommendation service using event streams, vector scoring, and Redis feature caching.",
    version="0.2.0",
)

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
USER_EVENTS_TOPIC = os.getenv("USER_EVENTS_TOPIC", "user-events")
CATALOG_PATH = Path(os.getenv("CATALOG_PATH", Path(__file__).with_name("catalog.json")))

r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)


def load_catalog() -> list[dict[str, Any]]:
    with CATALOG_PATH.open(encoding="utf-8") as catalog_file:
        return json.load(catalog_file)


ITEM_CATALOG = load_catalog()


class InteractionEvent(BaseModel):
    user_id: int
    item_id: str
    event_type: str = Field(default="view", examples=["view", "like", "complete"])
    rating: float | None = Field(default=None, ge=0, le=5)
    context: str | None = Field(default=None, examples=["learning", "backend", "genai"])


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


def profile_key(user_id: int) -> str:
    return f"user-profile:{user_id}"


def recommendations_key(user_id: int) -> str:
    return f"recommendations:{user_id}"


def load_profile(user_id: int) -> dict[str, Any]:
    raw_profile = r.get(profile_key(user_id))
    if raw_profile:
        return json.loads(raw_profile)
    return {"user_id": user_id, "vector": default_user_vector(), "events": []}


def save_profile(profile: dict[str, Any]) -> None:
    r.set(profile_key(profile["user_id"]), json.dumps(profile))


def context_boost(item: dict[str, Any], context: str | None) -> float:
    if not context:
        return 0
    normalized_context = context.lower()
    return 0.12 if normalized_context in item["tags"] or normalized_context in item["title"].lower() else 0


def rank_recommendations(user_id: int, context: str | None = None, limit: int = 5) -> list[dict[str, Any]]:
    profile = load_profile(user_id)
    user_vector = profile["vector"]
    ranked_items = []

    for item in ITEM_CATALOG:
        semantic_score = cosine_similarity(user_vector, item["vector"])
        popularity_score = item["popularity"] * 0.15
        exploration_score = random.uniform(0, 0.03)
        final_score = semantic_score + popularity_score + context_boost(item, context) + exploration_score
        ranked_items.append(
            {
                "item_id": item["item_id"],
                "title": item["title"],
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
    recommendations = ranked_items[:limit]
    r.set(recommendations_key(user_id), json.dumps(recommendations), ex=900)
    return recommendations


def update_profile_from_interaction(event: InteractionEvent) -> dict[str, Any]:
    profile = load_profile(event.user_id)
    matched_item = next((item for item in ITEM_CATALOG if item["item_id"] == event.item_id), None)
    if not matched_item:
        return profile

    weight = {"view": 0.10, "like": 0.22, "complete": 0.30}.get(event.event_type, 0.08)
    if event.rating is not None:
        weight += event.rating / 25

    profile["vector"] = [
        round((current * (1 - weight)) + (incoming * weight), 4)
        for current, incoming in zip(profile["vector"], matched_item["vector"])
    ]
    profile["events"] = (profile.get("events", []) + [event.dict()])[-20:]
    save_profile(profile)
    rank_recommendations(event.user_id, event.context)
    return profile


def process_event(event_data: dict[str, Any]) -> None:
    print(f"Received event: {event_data}")
    user_id = int(event_data["user_id"])
    profile = {
        "user_id": user_id,
        "username": event_data.get("username"),
        "vector": default_user_vector(event_data),
        "events": [event_data],
    }
    save_profile(profile)
    rank_recommendations(user_id)


def consume_events() -> None:
    consumer = None
    while consumer is None:
        try:
            consumer = KafkaConsumer(
                USER_EVENTS_TOPIC,
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                group_id="recommendation-service",
                value_deserializer=lambda message: json.loads(message.decode("utf-8")),
            )
        except NoBrokersAvailable:
            print("Kafka broker unavailable, retrying in 3 seconds...")
            time.sleep(3)

    for message in consumer:
        process_event(message.value)


def start_consumer() -> None:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_in_executor(None, consume_events)


@app.on_event("startup")
async def on_startup() -> None:
    threading.Thread(target=start_consumer, daemon=True).start()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "recommendation-ai"}


@app.get("/recommendations/{user_id}")
async def get_recommendations(user_id: int, context: str | None = None, limit: int = 5) -> dict[str, Any]:
    cached_recommendations = r.get(recommendations_key(user_id))
    if cached_recommendations and context is None:
        recommendations = json.loads(cached_recommendations)
    else:
        recommendations = rank_recommendations(user_id, context, limit)

    return {
        "user_id": user_id,
        "model": "hybrid-content-vector-ranker-v0",
        "feature_store": "redis",
        "recommendations": recommendations[:limit],
    }


@app.post("/events/interaction")
async def record_interaction(event: InteractionEvent) -> dict[str, Any]:
    profile = update_profile_from_interaction(event)
    return {
        "message": "interaction recorded",
        "user_id": event.user_id,
        "updated_profile_vector": profile["vector"],
        "next_best_recommendations": rank_recommendations(event.user_id, event.context, limit=3),
    }
