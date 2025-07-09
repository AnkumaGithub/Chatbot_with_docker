FROM --platform=linux/arm64 python:3.11-slim

RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    libopenblas-dev \
    librdkafka-dev \
    && rm -rf /var/lib/apt/lists/*

# PyTorch для ARM
RUN pip install --no-cache-dir \
    torch \
    torchvision \
    torchaudio \
    --index-url https://download.pytorch.org/whl/nightly/cpu

RUN pip install --no-cache-dir \
    transformers==4.53.1 \
    accelerate==1.8.1 \
    fastapi==0.115.14 \
    uvicorn==0.35.0 \
    python-dotenv==1.0.0 \
    confluent_kafka==2.11.0 \
    prometheus-client==0.22.1 \
    prometheus-fastapi-instrumentator==7.1.0

WORKDIR /app

COPY src_llm/llm.py .
COPY src_llm/server.py .
COPY src_llm/kafka_utils.py .

RUN python3 -c "\
from transformers import AutoModel; \
model = AutoModel.from_pretrained('gpt2'); \
print('GPT-2 model successfully loaded!')"

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]