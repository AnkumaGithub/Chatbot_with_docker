FROM --platform=linux/arm64 python:3.11-slim

RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    libopenblas-dev \
    librdkafka-dev \
    && rm -rf /var/lib/apt/lists/*

# Установка PyTorch для ARM
RUN pip install --no-cache-dir \
    torch \
    torchvision \
    torchaudio \
    --index-url https://download.pytorch.org/whl/nightly/cpu

RUN pip install --no-cache-dir \
    transformers==4.40.0 \
    accelerate==0.30.0 \
    fastapi==0.110.0 \
    uvicorn==0.29.0 \
    python-dotenv==1.0.0 \
    confluent-kafka==2.3.0

WORKDIR /app

COPY src/llm.py .
COPY src/server.py .
COPY src/kafka_utils.py .

# Предварительная загрузка модели GPT-2
RUN python3 -c "\
from transformers import AutoModel; \
model = AutoModel.from_pretrained('gpt2'); \
print('GPT-2 model successfully loaded!')"

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]