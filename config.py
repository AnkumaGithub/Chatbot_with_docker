import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
    REQUEST_TOPIC = os.getenv("REQUEST_TOPIC", "user_requests")
    RESPONSE_TOPIC = os.getenv("RESPONSE_TOPIC", "model_responses")
    QDRANT_URL = os.getenv("QDRANT_URL")
    QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "cache")
    AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
    AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")
    S3_BUCKET = os.getenv("S3_BUCKET")