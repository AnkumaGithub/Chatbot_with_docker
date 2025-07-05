from fastapi import FastAPI
from pydantic import BaseModel
from llm import generate_text
import torch
import threading
from kafka_utils import REQUEST_TOPIC, RESPONSE_TOPIC, create_producer, create_consumer, serialize_message, \
    deserialize_message, delivery_report

app = FastAPI()
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")


def kafka_worker():
    print("Starting Kafka worker...")
    consumer = create_consumer()
    consumer.subscribe([REQUEST_TOPIC])
    producer = create_producer()

    while True:
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            print(f"Consumer error: {msg.error()}")
            continue

        try:
            request = deserialize_message(msg.value())
            print(f"Received request: {request['correlation_id']}")

            # Выполняем генерацию текста
            result = generate_text(request['prompt'], device)

            # Отправляем ответ
            response = {
                "correlation_id": request['correlation_id'],
                "generated_text": result
            }
            producer.produce(
                topic=RESPONSE_TOPIC,
                value=serialize_message(response),
                callback=delivery_report
            )
            producer.flush()
            print(f"Sent response: {request['correlation_id']}")

        except Exception as e:
            print(f"Processing error: {str(e)}")


@app.on_event("startup")
def startup_event():
    # Запускаем обработчик Kafka в отдельном потоке
    threading.Thread(target=kafka_worker, daemon=True).start()
    print("Kafka worker started")


@app.get("/health")
async def health_check():
    return {"status": "ok", "device": str(device)}