from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel
import uuid
import asyncio
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

# Словарь для отслеживания ожидающих запросов
pending_requests = {}


class GenerationRequest(BaseModel):
    prompt: str


@app.post("/generate")
async def generate_text_api(request: GenerationRequest):
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
        return response
    except asyncio.TimeoutError:
        return {"error": "LLM service timeout"}


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(consume_responses())


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