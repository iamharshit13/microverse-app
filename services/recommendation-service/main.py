# from fastapi import FastAPI

# app = FastAPI()

# @app.get("/")
# def read_root():
#     return {"message": "Hello, World!"}

from fastapi import FastAPI
from kafka import KafkaConsumer
import json
import redis
import threading
import asyncio

app = FastAPI()

# Initialize Redis connection
r = redis.Redis(host='localhost', port=6379, db=0)

def consume_events():
    consumer = KafkaConsumer(
        'user-events',  # Kafka topic to listen to
        bootstrap_servers='localhost:9092',  # Kafka broker
        group_id='recommendation-service',
        value_deserializer=lambda m: json.loads(m.decode('utf-8'))
    )
    for message in consumer:
        process_event(message.value)

def process_event(event_data):
    # Process event data, generate recommendations and cache in Redis
    print(f"Received event: {event_data}")
    user_id = event_data['user_id']
    recommendation = f"Recommendations for {event_data['username']}"
    r.set(user_id, recommendation)

def start_consumer():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_in_executor(None, consume_events)

@app.on_event("startup")
async def on_startup():
    # Start Kafka consumer in a separate thread
    threading.Thread(target=start_consumer, daemon=True).start()

@app.get("/recommendations/{user_id}")
async def get_recommendations(user_id: int):
    recommendation = r.get(user_id)
    if recommendation:
        return {"user_id": user_id, "recommendation": recommendation.decode('utf-8')}
    return {"user_id": user_id, "recommendation": "No recommendations available."}
