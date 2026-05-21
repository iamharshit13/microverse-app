import asyncio
import json
import os
import threading
import time
from pathlib import Path
from typing import Any

import redis
import psycopg2
from psycopg2.extras import Json
from fastapi import FastAPI
from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable
from pydantic import BaseModel, Field
from recommender import default_user_vector, load_catalog, rank_items, update_profile_vector


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
DB_NAME = os.getenv("DB_NAME", "microverse")
DB_USER = os.getenv("DB_USER", "microverse")
DB_PASSWORD = os.getenv("DB_PASSWORD", "microverse")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")

r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)
ITEM_CATALOG = load_catalog(CATALOG_PATH)


class InteractionEvent(BaseModel):
    user_id: int
    item_id: str
    event_type: str = Field(default="view", examples=["view", "like", "complete"])
    rating: float | None = Field(default=None, ge=0, le=5)
    context: str | None = Field(default=None, examples=["learning", "backend", "genai"])


def profile_key(user_id: int) -> str:
    return f"user-profile:{user_id}"


def recommendations_key(user_id: int) -> str:
    return f"recommendations:{user_id}"


def get_db_connection():
    return psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
    )


def init_database() -> None:
    while True:
        try:
            with get_db_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        CREATE TABLE IF NOT EXISTS recommendation_interactions (
                            id SERIAL PRIMARY KEY,
                            user_id INTEGER NOT NULL,
                            item_id TEXT NOT NULL,
                            event_type TEXT NOT NULL,
                            rating NUMERIC,
                            context TEXT,
                            payload JSONB NOT NULL,
                            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                        )
                        """
                    )
                    cursor.execute(
                        """
                        CREATE TABLE IF NOT EXISTS recommendation_snapshots (
                            id SERIAL PRIMARY KEY,
                            user_id INTEGER NOT NULL,
                            context TEXT,
                            model TEXT NOT NULL,
                            recommendations JSONB NOT NULL,
                            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                        )
                        """
                    )
                    cursor.execute(
                        """
                        CREATE INDEX IF NOT EXISTS recommendation_interactions_user_id_idx
                        ON recommendation_interactions (user_id)
                        """
                    )
                    cursor.execute(
                        """
                        CREATE INDEX IF NOT EXISTS recommendation_snapshots_user_id_idx
                        ON recommendation_snapshots (user_id)
                        """
                    )
            return
        except psycopg2.OperationalError:
            print("Postgres unavailable, retrying in 3 seconds...")
            time.sleep(3)


def persist_recommendation_snapshot(
    user_id: int,
    context: str | None,
    recommendations: list[dict[str, Any]],
) -> None:
    try:
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO recommendation_snapshots (user_id, context, model, recommendations)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (user_id, context, "hybrid-content-vector-ranker-v0", Json(recommendations)),
                )
    except psycopg2.Error as error:
        print(f"Could not persist recommendation snapshot: {error}")


def persist_interaction(event: InteractionEvent) -> None:
    try:
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO recommendation_interactions
                        (user_id, item_id, event_type, rating, context, payload)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        event.user_id,
                        event.item_id,
                        event.event_type,
                        event.rating,
                        event.context,
                        Json(event.dict()),
                    ),
                )
    except psycopg2.Error as error:
        print(f"Could not persist interaction: {error}")


def load_profile(user_id: int) -> dict[str, Any]:
    raw_profile = r.get(profile_key(user_id))
    if raw_profile:
        return json.loads(raw_profile)
    return {"user_id": user_id, "vector": default_user_vector(), "events": []}


def save_profile(profile: dict[str, Any]) -> None:
    r.set(profile_key(profile["user_id"]), json.dumps(profile))


def rank_recommendations(user_id: int, context: str | None = None, limit: int = 5) -> list[dict[str, Any]]:
    profile = load_profile(user_id)
    recommendations = rank_items(ITEM_CATALOG, profile["vector"], context, limit)
    r.set(recommendations_key(user_id), json.dumps(recommendations), ex=900)
    persist_recommendation_snapshot(user_id, context, recommendations)
    return recommendations


def update_profile_from_interaction(event: InteractionEvent) -> dict[str, Any]:
    profile = load_profile(event.user_id)
    matched_item = next((item for item in ITEM_CATALOG if item["item_id"] == event.item_id), None)
    if not matched_item:
        return profile

    profile["vector"] = update_profile_vector(
        profile["vector"],
        matched_item["vector"],
        event.event_type,
        event.rating,
    )
    profile["events"] = (profile.get("events", []) + [event.dict()])[-20:]
    save_profile(profile)
    persist_interaction(event)
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
    init_database()
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
        "profile": load_profile(user_id),
        "recommendations": recommendations[:limit],
    }


@app.get("/profiles/{user_id}")
async def get_profile(user_id: int) -> dict[str, Any]:
    return load_profile(user_id)


@app.get("/catalog")
async def get_catalog() -> dict[str, Any]:
    return {"items": ITEM_CATALOG, "count": len(ITEM_CATALOG)}


@app.get("/history/{user_id}")
async def get_history(user_id: int, limit: int = 10) -> dict[str, Any]:
    try:
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT item_id, event_type, rating, context, created_at
                    FROM recommendation_interactions
                    WHERE user_id = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (user_id, limit),
                )
                interactions = [
                    {
                        "item_id": row[0],
                        "event_type": row[1],
                        "rating": float(row[2]) if row[2] is not None else None,
                        "context": row[3],
                        "created_at": row[4].isoformat(),
                    }
                    for row in cursor.fetchall()
                ]
    except psycopg2.Error as error:
        return {"user_id": user_id, "interactions": [], "error": str(error)}

    return {"user_id": user_id, "interactions": interactions}


@app.post("/events/interaction")
async def record_interaction(event: InteractionEvent) -> dict[str, Any]:
    profile = update_profile_from_interaction(event)
    return {
        "message": "interaction recorded",
        "user_id": event.user_id,
        "updated_profile_vector": profile["vector"],
        "next_best_recommendations": rank_recommendations(event.user_id, event.context, limit=3),
    }
