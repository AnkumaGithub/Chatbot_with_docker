from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel
import uuid
import asyncio
from qdrant_client import QdrantClient
from qdrant_client.http import models
from sentence_transformers import SentenceTransformer
from kafka_utils import (
    REQUEST_TOPIC,
    RESPONSE_TOPIC,
    create_producer,
    deserialize_message,
    serialize_message,
    delivery_report as kafka_delivery_report
)

app = FastAPI()
load_dotenv()

QDRANT_URL = "http://qdrant-service:6333"
COLLECTION_NAME = "prompt_cache"
EMBEDDING_MODEL = 'all-MiniLM-L6-v2'
SIMILARITY_THRESHOLD = 0.95

encoder = None
qdrant_client = None
pending_requests = {}


class GenerationRequest(BaseModel):
    prompt: str


@app.on_event("startup")
async def startup_event():
    global encoder, qdrant_client

    encoder = SentenceTransformer(EMBEDDING_MODEL)

    qdrant_client = QdrantClient(QDRANT_URL, timeout=10)

    try:
        qdrant_client.get_collection(COLLECTION_NAME)
    except Exception:
        qdrant_client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(
                size=encoder.get_sentence_embedding_dimension(),
                distance=models.Distance.COSINE,
            )
        )

    asyncio.create_task(consume_responses())


def get_embedding(text: str) -> list:
    return encoder.encode(text).tolist()


async def find_similar_prompt(prompt: str) -> dict:
    embedding = get_embedding(prompt)
    search_result = qdrant_client.search(
        collection_name=COLLECTION_NAME,
        query_vector=embedding,
        limit=1,
        score_threshold=SIMILARITY_THRESHOLD
    )
    return search_result[0].payload if search_result else None


async def cache_prompt_response(prompt: str, response: dict):
    embedding = get_embedding(prompt)
    point_id = str(uuid.uuid4())
    qdrant_client.upsert(
        collection_name=COLLECTION_NAME,
        points=[
            models.PointStruct(
                id=point_id,
                vector=embedding,
                payload={
                    "prompt": prompt,
                    "response": response
                }
            )
        ]
    )


@app.post("/generate")
async def generate_text_api(request: GenerationRequest):
    cached = await find_similar_prompt(request.prompt)
    if cached:
        return cached["response"]

    correlation_id = str(uuid.uuid4())

    producer = create_producer()
    kafka_message = {
        "correlation_id": correlation_id,
        "prompt": request.prompt
    }
    producer.produce(
        topic=REQUEST_TOPIC,
        value=serialize_message(kafka_message),
        callback=kafka_delivery_report
    )
    producer.flush()

    future = asyncio.Future()
    pending_requests[correlation_id] = future

    try:
        response = await asyncio.wait_for(future, timeout=180.0)
        await cache_prompt_response(request.prompt, response)
        return response
    except asyncio.TimeoutError:
        return {"error": "LLM service timeout"}


async def consume_responses():
    from kafka_utils import create_consumer, deserialize_message, RESPONSE_TOPIC

    consumer = create_consumer()
    consumer.subscribe([RESPONSE_TOPIC])

    while True:
        msg = consumer.poll(1.0)
        if msg is None:
            await asyncio.sleep(0.1)
            continue
        if msg.error():
            print(f"Consumer error: {msg.error()}")
            continue

        try:
            response = deserialize_message(msg.value())
            corr_id = response.get('correlation_id')

            if corr_id in pending_requests:
                pending_requests[corr_id].set_result(response)
                del pending_requests[corr_id]
        except Exception as e:
            print(f"Error processing response: {str(e)}")


@app.get("/health")
async def health_check():
    return {"status": "ok"}