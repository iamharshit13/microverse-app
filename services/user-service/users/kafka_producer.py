from kafka import KafkaProducer
import json

def get_kafka_producer():
    return KafkaProducer(
        bootstrap_servers='localhost:9092',  # Kafka broker URL
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )

def send_event(topic, event_data):
    producer = get_kafka_producer()
    producer.send(topic, event_data)
    producer.flush()
