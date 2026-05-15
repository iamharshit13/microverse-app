import json
import os
import time

from kafka import KafkaProducer
from kafka.errors import KafkaError, NoBrokersAvailable


KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

def get_kafka_producer():
    last_error = None
    for _ in range(5):
        try:
            return KafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
        except NoBrokersAvailable as error:
            last_error = error
            time.sleep(2)
    raise last_error

def send_event(topic, event_data):
    try:
        producer = get_kafka_producer()
        producer.send(topic, event_data)
        producer.flush()
        producer.close()
    except KafkaError as error:
        print(f"Kafka publish failed: {error}")
