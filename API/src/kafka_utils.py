from confluent_kafka import Producer, Consumer
import json

KAFKA_BOOTSTRAP_SERVERS = "kafka-service:9092"
REQUEST_TOPIC = "generation_requests"
RESPONSE_TOPIC = "generation_responses"

def create_producer():
    return Producer({
        'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
        'message.max.bytes': 15728640  # 15MB
    })

def create_consumer(group_id="llm-worker-group"):
    return Consumer({
        'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
        'group.id': group_id,
        'auto.offset.reset': 'earliest'
    })

def delivery_report(err, msg):
    if err:
        print(f'Message delivery failed: {err}')
    else:
        print(f'Message delivered to {msg.topic()} [{msg.partition()}]')

def serialize_message(message):
    return json.dumps(message).encode('utf-8')

def deserialize_message(msg_value):
    return json.loads(msg_value.decode('utf-8'))